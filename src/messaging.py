"""Client messaging layer for sending structured data to the frontend.

Provides ``ClientMessenger``, a flexible abstraction over LiveKit's data
channel that lets the agent push typed JSON messages to connected clients
during a voice session.  Analogous to ElevenLabs' "Client Tools" concept.

Usage in a tool or hook::

    messenger = ClientMessenger(room)

    # RAG results with relevance score
    await messenger.send("rag_result", {
        "query": "company policy",
        "chunks": [...],
        "relevance": 0.92,
    })

    # Arbitrary status / UI updates
    await messenger.send("status", {"stage": "searching"})

On the frontend, listen for data messages on the room and parse the JSON
envelope (see README for React example).
"""
import json
import logging
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any

from livekit import rtc

logger = logging.getLogger("messaging")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# The LiveKit data-channel *topic* used for all agent→client messages.
# Clients subscribe to this topic to receive structured messages.
AGENT_MESSAGE_TOPIC = "agent:message"


class DeliveryMode(str, Enum):
    """How the message is delivered over the data channel.

    - ``RELIABLE``: TCP-like – guaranteed delivery, ordered.  Best for
      important payloads like RAG results or UI state changes.
    - ``LOSSY``: UDP-like – low latency, no delivery guarantee.  Good for
      high-frequency updates (progress bars, live indicators).
    """

    RELIABLE = "reliable"
    LOSSY = "lossy"


# ---------------------------------------------------------------------------
# Message envelope
# ---------------------------------------------------------------------------

@dataclass
class ClientMessage:
    """Wire-format envelope sent over the data channel.

    Every message has a ``type`` (your domain event name) and a free-form
    ``payload`` dict.  ``timestamp`` is set automatically so the client can
    order / deduplicate messages.
    """

    type: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

    def to_bytes(self) -> bytes:
        return self.to_json().encode("utf-8")

    @classmethod
    def from_json(cls, raw: str | bytes) -> "ClientMessage":
        data = json.loads(raw)
        return cls(
            type=data["type"],
            payload=data.get("payload", {}),
            timestamp=data.get("timestamp", time.time()),
        )


# ---------------------------------------------------------------------------
# Core messenger
# ---------------------------------------------------------------------------

class ClientMessenger:
    """Sends structured messages to the frontend via LiveKit data channel.

    Instantiate once per session with the LiveKit ``Room``, then call
    :meth:`send` from anywhere (tools, hooks, agent methods).

    Args:
        room: The LiveKit ``rtc.Room`` instance for the current session.
        default_mode: Default delivery mode (``RELIABLE`` or ``LOSSY``).
    """

    def __init__(
        self,
        room: rtc.Room,
        *,
        default_mode: DeliveryMode = DeliveryMode.RELIABLE,
    ) -> None:
        self._room = room
        self._default_mode = default_mode
        self._history: list[ClientMessage] = []

    # -- public API --------------------------------------------------------

    async def send(
        self,
        msg_type: str,
        payload: dict[str, Any] | None = None,
        *,
        mode: DeliveryMode | None = None,
        destination_identities: list[str] | None = None,
    ) -> ClientMessage:
        """Send a typed message to the frontend client(s).

        Args:
            msg_type: A domain event name (e.g. ``"rag_result"``,
                ``"status"``, ``"ui_update"``).
            payload: Arbitrary JSON-serialisable data.
            mode: Override the default delivery mode for this message.
            destination_identities: Send only to specific participants
                (by identity string).  ``None`` broadcasts to everyone.

        Returns:
            The ``ClientMessage`` that was sent (useful for logging / tests).
        """
        message = ClientMessage(type=msg_type, payload=payload or {})
        effective_mode = mode or self._default_mode

        kind = (
            rtc.DataPacketKind.KIND_RELIABLE
            if effective_mode == DeliveryMode.RELIABLE
            else rtc.DataPacketKind.KIND_LOSSY
        )

        publish_kwargs: dict[str, Any] = {
            "payload": message.to_bytes(),
            "kind": kind,
            "topic": AGENT_MESSAGE_TOPIC,
        }
        if destination_identities:
            publish_kwargs["destination_identities"] = destination_identities

        await self._room.local_participant.publish_data(**publish_kwargs)

        self._history.append(message)
        logger.debug("Sent %s message: %s", msg_type, message.to_json())

        return message

    # -- convenience helpers -----------------------------------------------

    async def send_rag_result(
        self,
        query: str,
        chunks: list[dict[str, Any]],
        *,
        relevance: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ClientMessage:
        """Send RAG retrieval results to the client.

        This is a typed convenience wrapper around :meth:`send`.

        Args:
            query: The search query that was used.
            chunks: List of retrieved chunks, each a dict with at least
                ``"text"`` and optionally ``"score"``, ``"source"``, etc.
            relevance: Overall relevance score (0.0 – 1.0).
            metadata: Extra metadata to include.
        """
        payload: dict[str, Any] = {
            "query": query,
            "chunks": chunks,
        }
        if relevance is not None:
            payload["relevance"] = relevance
        if metadata:
            payload["metadata"] = metadata
        return await self.send("rag_result", payload)

    async def send_status(
        self,
        stage: str,
        *,
        progress: float | None = None,
        detail: str = "",
    ) -> ClientMessage:
        """Send a status / progress update to the client.

        Args:
            stage: Short label (e.g. ``"searching"``, ``"generating"``).
            progress: Optional 0.0 – 1.0 progress fraction.
            detail: Optional human-readable detail string.
        """
        payload: dict[str, Any] = {"stage": stage}
        if progress is not None:
            payload["progress"] = progress
        if detail:
            payload["detail"] = detail
        return await self.send("status", payload)

    async def send_tool_result(
        self,
        tool_name: str,
        result: dict[str, Any],
    ) -> ClientMessage:
        """Notify the client that a tool produced a result.

        Useful for showing tool outputs in a client-side panel.
        """
        return await self.send("tool_result", {
            "tool": tool_name,
            "result": result,
        })

    async def send_error(
        self,
        code: str,
        message: str,
        *,
        detail: dict[str, Any] | None = None,
    ) -> ClientMessage:
        """Send an error notification to the client."""
        payload: dict[str, Any] = {"code": code, "message": message}
        if detail:
            payload["detail"] = detail
        return await self.send("error", payload)

    # -- introspection -----------------------------------------------------

    @property
    def history(self) -> list[ClientMessage]:
        """All messages sent during this session (in order)."""
        return list(self._history)

    def clear_history(self) -> None:
        """Clear the in-memory message history."""
        self._history.clear()
