"""Configuration management for the voice agent."""
import os
from pathlib import Path
from typing import Any

import yaml
from dataclasses import dataclass, field

CONFIG_DIR = Path(__file__).parent.parent / "configs"


@dataclass
class AgentSettings:
    name: str = "Voice Assistant"
    system_prompt: str = "You are a helpful voice assistant."
    greeting: str = "Hello! How can I help you today?"
    max_history: int = 50


@dataclass
class STTSettings:
    provider: str = "deepgram"
    model: str = "nova-3"
    language: str = "multi"


@dataclass
class TTSSettings:
    provider: str = "openai"
    model: str = "gpt-4o-mini-tts"
    voice: str = "coral"
    elevenlabs_voice_id: str = ""
    elevenlabs_model: str = "eleven_turbo_v2_5"


@dataclass
class LLMSettings:
    provider: str = "openai"
    model: str = "gpt-4o"
    temperature: float = 0.7


@dataclass
class VADSettings:
    threshold: float = 0.5
    min_silence_ms: int = 600
    min_speech_ms: int = 250


@dataclass
class TurnDetectionSettings:
    type: str = "multilingual"
    allow_interruptions: bool = True


@dataclass
class EmotionSettings:
    enabled: bool = True
    adaptive_prompts: dict[str, str] = field(default_factory=dict)


@dataclass
class ToolParameter:
    name: str
    type: str = "string"
    description: str = ""
    required: bool = False


@dataclass
class ToolConfig:
    name: str
    description: str
    parameters: list[ToolParameter] = field(default_factory=list)
    webhook_url: str = ""


@dataclass
class Config:
    agent: AgentSettings = field(default_factory=AgentSettings)
    stt: STTSettings = field(default_factory=STTSettings)
    tts: TTSSettings = field(default_factory=TTSSettings)
    llm: LLMSettings = field(default_factory=LLMSettings)
    vad: VADSettings = field(default_factory=VADSettings)
    turn_detection: TurnDetectionSettings = field(default_factory=TurnDetectionSettings)
    emotion: EmotionSettings = field(default_factory=EmotionSettings)
    tools: list[ToolConfig] = field(default_factory=list)


def load_config(config_path: str | None = None) -> Config:
    """Load configuration from YAML file.

    Args:
        config_path: Path to the YAML configuration file. If None, uses the
            AGENT_CONFIG environment variable or falls back to configs/default.yaml.

    Returns:
        A fully populated Config dataclass instance.
    """
    if config_path is None:
        config_path = os.environ.get("AGENT_CONFIG", str(CONFIG_DIR / "default.yaml"))

    path = Path(config_path)
    if not path.exists():
        return Config()

    with open(path) as f:
        data = yaml.safe_load(f) or {}

    config = Config()

    # Parse agent settings
    if "agent" in data:
        a = data["agent"]
        config.agent = AgentSettings(
            name=a.get("name", config.agent.name),
            system_prompt=a.get("system_prompt", config.agent.system_prompt),
            greeting=a.get("greeting", config.agent.greeting),
            max_history=a.get("max_history", config.agent.max_history),
        )

    # Parse STT
    if "stt" in data:
        s = data["stt"]
        config.stt = STTSettings(
            provider=s.get("provider", config.stt.provider),
            model=s.get("model", config.stt.model),
            language=s.get("language", config.stt.language),
        )

    # Parse TTS
    if "tts" in data:
        t = data["tts"]
        config.tts = TTSSettings(
            provider=t.get("provider", config.tts.provider),
            model=t.get("model", config.tts.model),
            voice=t.get("voice", config.tts.voice),
            elevenlabs_voice_id=t.get("elevenlabs_voice_id", config.tts.elevenlabs_voice_id),
            elevenlabs_model=t.get("elevenlabs_model", config.tts.elevenlabs_model),
        )

    # Parse LLM
    if "llm" in data:
        ll = data["llm"]
        config.llm = LLMSettings(
            provider=ll.get("provider", config.llm.provider),
            model=ll.get("model", config.llm.model),
            temperature=ll.get("temperature", config.llm.temperature),
        )

    # Parse VAD
    if "vad" in data:
        v = data["vad"]
        config.vad = VADSettings(
            threshold=v.get("threshold", config.vad.threshold),
            min_silence_ms=v.get("min_silence_ms", config.vad.min_silence_ms),
            min_speech_ms=v.get("min_speech_ms", config.vad.min_speech_ms),
        )

    # Parse turn detection
    if "turn_detection" in data:
        td = data["turn_detection"]
        config.turn_detection = TurnDetectionSettings(
            type=td.get("type", config.turn_detection.type),
            allow_interruptions=td.get(
                "allow_interruptions", config.turn_detection.allow_interruptions
            ),
        )

    # Parse emotion
    if "emotion" in data:
        e = data["emotion"]
        config.emotion = EmotionSettings(
            enabled=e.get("enabled", config.emotion.enabled),
            adaptive_prompts=e.get("adaptive_prompts", {}),
        )

    # Parse tools
    if "tools" in data:
        config.tools = []
        for tool_data in data["tools"]:
            params = []
            for p in tool_data.get("parameters", []):
                params.append(
                    ToolParameter(
                        name=p["name"],
                        type=p.get("type", "string"),
                        description=p.get("description", ""),
                        required=p.get("required", False),
                    )
                )
            config.tools.append(
                ToolConfig(
                    name=tool_data["name"],
                    description=tool_data.get("description", ""),
                    parameters=params,
                    webhook_url=tool_data.get("webhook_url", ""),
                )
            )

    return config
