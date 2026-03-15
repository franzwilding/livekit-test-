"""Production-ready AI Voice Agent using LiveKit Agents SDK.

This module is the main entry point for the voice agent. It wires together
configuration, emotional intelligence, tool support, and the LiveKit Agents
VoicePipelineAgent pattern using ``AgentSession`` and the ``Agent`` base class.
"""
import logging
import os

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
from livekit.plugins import deepgram, openai, silero, elevenlabs
from livekit.plugins import anthropic as anthropic_plugin
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from src.config import load_config, Config
from src.emotion import EmotionState, detect_emotion, get_emotion_prompt_addition
from src.hooks import AgentHooks
from src.tools import BUILTIN_TOOLS

logger = logging.getLogger("voice-agent")

load_dotenv()
load_dotenv(".env.local")

# Load configuration at module level (can be overridden per-session)
config = load_config()


# ---------------------------------------------------------------------------
# Provider factory functions
# ---------------------------------------------------------------------------

def create_stt(cfg: Config):
    """Create a Speech-to-Text instance based on config.

    Args:
        cfg: The loaded agent configuration.

    Returns:
        An STT plugin instance (Deepgram or OpenAI).

    Raises:
        ValueError: If the configured provider is not supported.
    """
    if cfg.stt.provider == "deepgram":
        return deepgram.STT(model=cfg.stt.model, language=cfg.stt.language)
    elif cfg.stt.provider == "openai":
        return openai.STT(model=cfg.stt.model, language=cfg.stt.language)
    raise ValueError(f"Unknown STT provider: {cfg.stt.provider}")


def create_tts(cfg: Config):
    """Create a Text-to-Speech instance based on config.

    Args:
        cfg: The loaded agent configuration.

    Returns:
        A TTS plugin instance (OpenAI or ElevenLabs).

    Raises:
        ValueError: If the configured provider is not supported.
    """
    if cfg.tts.provider == "openai":
        return openai.TTS(model=cfg.tts.model, voice=cfg.tts.voice)
    elif cfg.tts.provider == "elevenlabs":
        voice_id = cfg.tts.elevenlabs_voice_id or cfg.tts.voice
        return elevenlabs.TTS(
            model=cfg.tts.elevenlabs_model,
            voice=(
                elevenlabs.Voice(id=voice_id)
                if cfg.tts.elevenlabs_voice_id
                else elevenlabs.Voice(name=cfg.tts.voice)
            ),
        )
    raise ValueError(f"Unknown TTS provider: {cfg.tts.provider}")


def create_llm(cfg: Config):
    """Create an LLM instance based on config.

    Args:
        cfg: The loaded agent configuration.

    Returns:
        An LLM plugin instance (OpenAI or Anthropic).

    Raises:
        ValueError: If the configured provider is not supported.
    """
    if cfg.llm.provider == "openai":
        return openai.LLM(model=cfg.llm.model, temperature=cfg.llm.temperature)
    elif cfg.llm.provider == "anthropic":
        return anthropic_plugin.LLM(model=cfg.llm.model, temperature=cfg.llm.temperature)
    raise ValueError(f"Unknown LLM provider: {cfg.llm.provider}")


def create_turn_detector(cfg: Config):
    """Create a turn detector based on config.

    Args:
        cfg: The loaded agent configuration.

    Returns:
        A turn detector instance, or ``None`` for silence-based detection.
    """
    if cfg.turn_detection.type == "multilingual":
        return MultilingualModel()
    return None


# ---------------------------------------------------------------------------
# Voice Assistant Agent
# ---------------------------------------------------------------------------

class VoiceAssistant(Agent):
    """Main voice assistant agent with emotional intelligence and tool support.

    Extends the LiveKit ``Agent`` base class, adding:
    - Emotion-aware system prompt augmentation via ``AgentHooks``
    - Built-in function tools (weather, web search, reminders)
    - Configurable instructions from YAML
    """

    def __init__(self, cfg: Config) -> None:
        self._cfg = cfg
        self._emotion_state = EmotionState()
        self._hooks = AgentHooks(
            emotion_state=self._emotion_state,
            adaptive_prompts=cfg.emotion.adaptive_prompts,
        )

        # Build dynamic instructions with emotion awareness
        instructions = cfg.agent.system_prompt
        if cfg.emotion.enabled:
            instructions += (
                "\n\nYou have emotional intelligence. Pay attention to the "
                "user's emotional state and adapt your responses accordingly."
            )

        super().__init__(instructions=instructions)

    @function_tool()
    async def get_weather(self, ctx: RunContext, location: str) -> str:
        """Get current weather for a location.

        Args:
            location: City name or address
        """
        handler = BUILTIN_TOOLS.get("get_weather")
        if handler:
            return await handler(location=location)
        return "Weather service unavailable."

    @function_tool()
    async def search_web(self, ctx: RunContext, query: str) -> str:
        """Search the web for information.

        Args:
            query: Search query
        """
        handler = BUILTIN_TOOLS.get("search_web")
        if handler:
            return await handler(query=query)
        return "Search service unavailable."

    @function_tool()
    async def set_reminder(self, ctx: RunContext, message: str, time: str) -> str:
        """Set a reminder for the user.

        Args:
            message: Reminder message
            time: When to remind (e.g., 'in 5 minutes', 'tomorrow at 9am')
        """
        handler = BUILTIN_TOOLS.get("set_reminder")
        if handler:
            return await handler(message=message, time=time)
        return "Reminder service unavailable."


# ---------------------------------------------------------------------------
# Agent server setup
# ---------------------------------------------------------------------------

server = AgentServer()


def prewarm(proc: JobProcess):
    """Prewarm: load the Silero VAD model once per worker process."""
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name=config.agent.name)
async def voice_agent_session(ctx: JobContext):
    """Handle an incoming voice agent session.

    Creates the pipeline components from configuration, instantiates the
    ``VoiceAssistant``, starts the session, and sends the initial greeting.
    """
    cfg = config  # Could reload per-session if needed

    session = AgentSession(
        stt=create_stt(cfg),
        llm=create_llm(cfg),
        tts=create_tts(cfg),
        vad=ctx.proc.userdata["vad"],
        turn_detection=create_turn_detector(cfg),
    )

    agent = VoiceAssistant(cfg)

    await session.start(
        agent=agent,
        room=ctx.room,
    )

    # Send greeting
    if cfg.agent.greeting:
        await session.generate_reply(
            instructions=f"Greet the user by saying: {cfg.agent.greeting}"
        )

    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
