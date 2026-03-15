"""AI Voice Agent using LiveKit Agents SDK."""
import logging

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    function_tool,
)
from livekit.plugins import deepgram, openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from src.messaging import ClientMessenger

logger = logging.getLogger("voice-agent")

load_dotenv()
load_dotenv(".env.local")

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

AGENT_NAME = "Voice Assistant"

SYSTEM_PROMPT = """\
You are a helpful, friendly voice assistant. Be concise and conversational.
Respond naturally as if speaking to a friend. Keep responses under 3 sentences
unless asked for detail. Use simple language suitable for speech."""

GREETING = "Hello! How can I help you today?"


# ---------------------------------------------------------------------------
# Voice Assistant Agent
# ---------------------------------------------------------------------------

class VoiceAssistant(Agent):

    def __init__(self, messenger: ClientMessenger | None = None) -> None:
        self._messenger = messenger
        super().__init__(instructions=SYSTEM_PROMPT)

    @property
    def messenger(self) -> ClientMessenger | None:
        return self._messenger

    # -- Tools (replace these demo implementations with real APIs) ---------

    @function_tool()
    async def get_weather(self, ctx: RunContext, location: str) -> str:
        """Get current weather for a location.

        Args:
            location: City name or address
        """
        return f"The weather in {location} is currently 22°C and sunny. Humidity is 45%."

    @function_tool()
    async def search_web(self, ctx: RunContext, query: str) -> str:
        """Search the web for information.

        Args:
            query: Search query
        """
        return f"Top results for '{query}': This is a demo. Connect a real search API."

    @function_tool()
    async def set_reminder(self, ctx: RunContext, message: str, time: str) -> str:
        """Set a reminder for the user.

        Args:
            message: Reminder message
            time: When to remind (e.g., 'in 5 minutes', 'tomorrow at 9am')
        """
        return f"Reminder set: '{message}' at {time}."


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name=AGENT_NAME)
async def voice_agent_session(ctx: JobContext):
    messenger = ClientMessenger(ctx.room)

    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=openai.LLM(model="gpt-4o", temperature=0.7),
        tts=openai.TTS(model="gpt-4o-mini-tts", voice="coral"),
        vad=ctx.proc.userdata["vad"],
        turn_detection=MultilingualModel(),
    )

    agent = VoiceAssistant(messenger=messenger)
    await session.start(agent=agent, room=ctx.room)

    if GREETING:
        await session.generate_reply(
            instructions=f"Greet the user by saying: {GREETING}"
        )

    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
