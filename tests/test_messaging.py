"""Tests for the client messaging layer.

Verifies message construction, serialisation, delivery mode routing,
convenience helpers, and history tracking — all without requiring
a real LiveKit connection.
"""
import json
import time

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.messaging import (
    AGENT_MESSAGE_TOPIC,
    ClientMessage,
    ClientMessenger,
    DeliveryMode,
)


# ---------------------------------------------------------------------------
# ClientMessage dataclass
# ---------------------------------------------------------------------------

class TestClientMessage:
    """Test the wire-format envelope."""

    def test_to_json_contains_type_and_payload(self):
        msg = ClientMessage(type="test", payload={"key": "value"})
        parsed = json.loads(msg.to_json())
        assert parsed["type"] == "test"
        assert parsed["payload"]["key"] == "value"
        assert "timestamp" in parsed

    def test_to_bytes_is_utf8(self):
        msg = ClientMessage(type="hello", payload={"emoji": "Hallo"})
        raw = msg.to_bytes()
        assert isinstance(raw, bytes)
        assert json.loads(raw.decode("utf-8"))["type"] == "hello"

    def test_from_json_string(self):
        original = ClientMessage(type="rag_result", payload={"score": 0.9})
        restored = ClientMessage.from_json(original.to_json())
        assert restored.type == "rag_result"
        assert restored.payload["score"] == 0.9

    def test_from_json_bytes(self):
        raw = b'{"type": "status", "payload": {"stage": "done"}}'
        msg = ClientMessage.from_json(raw)
        assert msg.type == "status"
        assert msg.payload["stage"] == "done"

    def test_from_json_missing_payload_defaults_to_empty(self):
        raw = '{"type": "ping"}'
        msg = ClientMessage.from_json(raw)
        assert msg.payload == {}

    def test_timestamp_auto_set(self):
        before = time.time()
        msg = ClientMessage(type="x")
        after = time.time()
        assert before <= msg.timestamp <= after

    def test_custom_timestamp(self):
        msg = ClientMessage(type="x", timestamp=1234567890.0)
        assert msg.timestamp == 1234567890.0

    def test_to_json_handles_non_serialisable_via_str(self):
        """Non-serialisable objects should be converted via str()."""
        msg = ClientMessage(type="test", payload={"path": "some/path"})
        parsed = json.loads(msg.to_json())
        assert parsed["payload"]["path"] == "some/path"


# ---------------------------------------------------------------------------
# Helpers for mocking the LiveKit room
# ---------------------------------------------------------------------------

def _make_mock_room():
    """Create a mock LiveKit Room with publish_data on local_participant."""
    room = MagicMock()
    room.local_participant = MagicMock()
    room.local_participant.publish_data = AsyncMock()
    return room


# ---------------------------------------------------------------------------
# ClientMessenger – send()
# ---------------------------------------------------------------------------

class TestClientMessengerSend:
    """Test the core send() method."""

    @pytest.mark.asyncio
    async def test_send_publishes_to_data_channel(self):
        room = _make_mock_room()
        messenger = ClientMessenger(room)

        msg = await messenger.send("test_event", {"foo": "bar"})

        room.local_participant.publish_data.assert_called_once()
        call_kwargs = room.local_participant.publish_data.call_args.kwargs
        assert call_kwargs["topic"] == AGENT_MESSAGE_TOPIC

        # Verify payload is valid JSON with correct structure
        payload_bytes = call_kwargs["payload"]
        parsed = json.loads(payload_bytes.decode("utf-8"))
        assert parsed["type"] == "test_event"
        assert parsed["payload"]["foo"] == "bar"

    @pytest.mark.asyncio
    async def test_send_reliable_by_default(self):
        room = _make_mock_room()
        messenger = ClientMessenger(room)

        await messenger.send("event", {})

        call_kwargs = room.local_participant.publish_data.call_args.kwargs
        # DataPacketKind.KIND_RELIABLE == 0
        from livekit import rtc
        assert call_kwargs["kind"] == rtc.DataPacketKind.KIND_RELIABLE

    @pytest.mark.asyncio
    async def test_send_lossy_mode(self):
        room = _make_mock_room()
        messenger = ClientMessenger(room)

        await messenger.send("event", {}, mode=DeliveryMode.LOSSY)

        call_kwargs = room.local_participant.publish_data.call_args.kwargs
        from livekit import rtc
        assert call_kwargs["kind"] == rtc.DataPacketKind.KIND_LOSSY

    @pytest.mark.asyncio
    async def test_send_default_mode_override(self):
        room = _make_mock_room()
        messenger = ClientMessenger(room, default_mode=DeliveryMode.LOSSY)

        await messenger.send("event", {})

        call_kwargs = room.local_participant.publish_data.call_args.kwargs
        from livekit import rtc
        assert call_kwargs["kind"] == rtc.DataPacketKind.KIND_LOSSY

    @pytest.mark.asyncio
    async def test_send_with_destination_identities(self):
        room = _make_mock_room()
        messenger = ClientMessenger(room)

        await messenger.send(
            "private", {"secret": True},
            destination_identities=["user_42"],
        )

        call_kwargs = room.local_participant.publish_data.call_args.kwargs
        assert call_kwargs["destination_identities"] == ["user_42"]

    @pytest.mark.asyncio
    async def test_send_without_destination_broadcasts(self):
        room = _make_mock_room()
        messenger = ClientMessenger(room)

        await messenger.send("broadcast", {})

        call_kwargs = room.local_participant.publish_data.call_args.kwargs
        assert "destination_identities" not in call_kwargs

    @pytest.mark.asyncio
    async def test_send_returns_client_message(self):
        room = _make_mock_room()
        messenger = ClientMessenger(room)

        result = await messenger.send("check", {"val": 1})

        assert isinstance(result, ClientMessage)
        assert result.type == "check"
        assert result.payload["val"] == 1

    @pytest.mark.asyncio
    async def test_send_empty_payload(self):
        room = _make_mock_room()
        messenger = ClientMessenger(room)

        msg = await messenger.send("ping")

        assert msg.payload == {}


# ---------------------------------------------------------------------------
# ClientMessenger – convenience helpers
# ---------------------------------------------------------------------------

class TestClientMessengerHelpers:
    """Test typed convenience methods."""

    @pytest.mark.asyncio
    async def test_send_rag_result(self):
        room = _make_mock_room()
        messenger = ClientMessenger(room)

        chunks = [
            {"text": "chunk 1", "score": 0.95, "source": "doc.pdf"},
            {"text": "chunk 2", "score": 0.72, "source": "faq.md"},
        ]
        msg = await messenger.send_rag_result(
            query="policy question",
            chunks=chunks,
            relevance=0.88,
            metadata={"index": "main"},
        )

        assert msg.type == "rag_result"
        assert msg.payload["query"] == "policy question"
        assert len(msg.payload["chunks"]) == 2
        assert msg.payload["relevance"] == 0.88
        assert msg.payload["metadata"]["index"] == "main"

    @pytest.mark.asyncio
    async def test_send_rag_result_minimal(self):
        room = _make_mock_room()
        messenger = ClientMessenger(room)

        msg = await messenger.send_rag_result(query="q", chunks=[])
        assert msg.type == "rag_result"
        assert "relevance" not in msg.payload
        assert "metadata" not in msg.payload

    @pytest.mark.asyncio
    async def test_send_status(self):
        room = _make_mock_room()
        messenger = ClientMessenger(room)

        msg = await messenger.send_status(
            "searching", progress=0.5, detail="Querying vector DB"
        )

        assert msg.type == "status"
        assert msg.payload["stage"] == "searching"
        assert msg.payload["progress"] == 0.5
        assert msg.payload["detail"] == "Querying vector DB"

    @pytest.mark.asyncio
    async def test_send_status_minimal(self):
        room = _make_mock_room()
        messenger = ClientMessenger(room)

        msg = await messenger.send_status("idle")
        assert msg.payload["stage"] == "idle"
        assert "progress" not in msg.payload
        assert "detail" not in msg.payload

    @pytest.mark.asyncio
    async def test_send_tool_result(self):
        room = _make_mock_room()
        messenger = ClientMessenger(room)

        msg = await messenger.send_tool_result(
            "weather", {"temp": 22, "unit": "C"}
        )

        assert msg.type == "tool_result"
        assert msg.payload["tool"] == "weather"
        assert msg.payload["result"]["temp"] == 22

    @pytest.mark.asyncio
    async def test_send_error(self):
        room = _make_mock_room()
        messenger = ClientMessenger(room)

        msg = await messenger.send_error(
            "RAG_TIMEOUT", "Vector search timed out",
            detail={"timeout_ms": 5000},
        )

        assert msg.type == "error"
        assert msg.payload["code"] == "RAG_TIMEOUT"
        assert msg.payload["message"] == "Vector search timed out"
        assert msg.payload["detail"]["timeout_ms"] == 5000

    @pytest.mark.asyncio
    async def test_send_error_minimal(self):
        room = _make_mock_room()
        messenger = ClientMessenger(room)

        msg = await messenger.send_error("GENERIC", "Something went wrong")
        assert "detail" not in msg.payload


# ---------------------------------------------------------------------------
# ClientMessenger – history
# ---------------------------------------------------------------------------

class TestClientMessengerHistory:
    """Test message history tracking."""

    @pytest.mark.asyncio
    async def test_history_records_sent_messages(self):
        room = _make_mock_room()
        messenger = ClientMessenger(room)

        await messenger.send("a", {"n": 1})
        await messenger.send("b", {"n": 2})
        await messenger.send("c", {"n": 3})

        assert len(messenger.history) == 3
        assert messenger.history[0].type == "a"
        assert messenger.history[2].type == "c"

    @pytest.mark.asyncio
    async def test_history_is_a_copy(self):
        room = _make_mock_room()
        messenger = ClientMessenger(room)

        await messenger.send("x", {})
        h = messenger.history
        h.clear()

        # Internal history should be unaffected
        assert len(messenger.history) == 1

    @pytest.mark.asyncio
    async def test_clear_history(self):
        room = _make_mock_room()
        messenger = ClientMessenger(room)

        await messenger.send("x", {})
        await messenger.send("y", {})
        messenger.clear_history()

        assert len(messenger.history) == 0

    def test_empty_history_on_init(self):
        room = _make_mock_room()
        messenger = ClientMessenger(room)
        assert messenger.history == []


# ---------------------------------------------------------------------------
# DeliveryMode enum
# ---------------------------------------------------------------------------

class TestDeliveryMode:
    def test_reliable_value(self):
        assert DeliveryMode.RELIABLE == "reliable"

    def test_lossy_value(self):
        assert DeliveryMode.LOSSY == "lossy"

    def test_is_string(self):
        assert isinstance(DeliveryMode.RELIABLE, str)


# ---------------------------------------------------------------------------
# Integration with VoiceAssistant
# ---------------------------------------------------------------------------

class TestVoiceAssistantMessengerIntegration:
    """Verify that VoiceAssistant exposes the messenger."""

    def test_messenger_property_when_set(self):
        with patch("src.agent.Agent.__init__", return_value=None):
            from src.agent import VoiceAssistant
            from src.config import Config

            room = _make_mock_room()
            messenger = ClientMessenger(room)
            cfg = Config()
            agent = VoiceAssistant(cfg, messenger=messenger)
            assert agent.messenger is messenger

    def test_messenger_property_none_by_default(self):
        with patch("src.agent.Agent.__init__", return_value=None):
            from src.agent import VoiceAssistant
            from src.config import Config

            cfg = Config()
            agent = VoiceAssistant(cfg)
            assert agent.messenger is None
