"""Tests for configuration management."""
import os
import tempfile
from pathlib import Path

import pytest
import yaml

from src.config import (
    AgentSettings,
    Config,
    LLMSettings,
    STTSettings,
    TTSSettings,
    ToolConfig,
    ToolParameter,
    TurnDetectionSettings,
    VADSettings,
    load_config,
)


# ---------------------------------------------------------------------------
# Default values
# ---------------------------------------------------------------------------

class TestDefaultConfig:

    def test_default_agent_settings(self):
        cfg = Config()
        assert cfg.agent.name == "Voice Assistant"
        assert cfg.agent.greeting == "Hello! How can I help you today?"
        assert cfg.agent.max_history == 50
        assert "helpful" in cfg.agent.system_prompt.lower()

    def test_default_stt(self):
        cfg = Config()
        assert cfg.stt.provider == "deepgram"
        assert cfg.stt.model == "nova-3"
        assert cfg.stt.language == "multi"

    def test_default_tts(self):
        cfg = Config()
        assert cfg.tts.provider == "openai"
        assert cfg.tts.model == "gpt-4o-mini-tts"
        assert cfg.tts.voice == "coral"
        assert cfg.tts.elevenlabs_voice_id == ""
        assert cfg.tts.elevenlabs_model == "eleven_turbo_v2_5"

    def test_default_llm(self):
        cfg = Config()
        assert cfg.llm.provider == "openai"
        assert cfg.llm.model == "gpt-4o"
        assert cfg.llm.temperature == 0.7

    def test_default_vad(self):
        cfg = Config()
        assert cfg.vad.threshold == 0.5
        assert cfg.vad.min_silence_ms == 600
        assert cfg.vad.min_speech_ms == 250

    def test_default_turn_detection(self):
        cfg = Config()
        assert cfg.turn_detection.type == "multilingual"
        assert cfg.turn_detection.allow_interruptions is True

    def test_default_tools_empty(self):
        cfg = Config()
        assert cfg.tools == []


# ---------------------------------------------------------------------------
# Loading from YAML
# ---------------------------------------------------------------------------

class TestLoadConfig:

    def _write_yaml(self, data: dict) -> str:
        fd, path = tempfile.mkstemp(suffix=".yaml")
        with os.fdopen(fd, "w") as f:
            yaml.dump(data, f)
        return path

    def test_load_missing_file_returns_defaults(self):
        cfg = load_config("/nonexistent/path/to/config.yaml")
        assert cfg.agent.name == "Voice Assistant"
        assert cfg.stt.provider == "deepgram"

    def test_load_empty_yaml(self):
        path = self._write_yaml({})
        try:
            cfg = load_config(path)
            assert cfg.agent.name == "Voice Assistant"
        finally:
            os.unlink(path)

    def test_load_agent_section(self):
        path = self._write_yaml({
            "agent": {
                "name": "TestBot",
                "system_prompt": "Be brief.",
                "greeting": "Hi!",
                "max_history": 10,
            }
        })
        try:
            cfg = load_config(path)
            assert cfg.agent.name == "TestBot"
            assert cfg.agent.system_prompt == "Be brief."
            assert cfg.agent.greeting == "Hi!"
            assert cfg.agent.max_history == 10
        finally:
            os.unlink(path)

    def test_load_stt_section(self):
        path = self._write_yaml({
            "stt": {"provider": "openai", "model": "whisper-1", "language": "en"}
        })
        try:
            cfg = load_config(path)
            assert cfg.stt.provider == "openai"
            assert cfg.stt.model == "whisper-1"
            assert cfg.stt.language == "en"
        finally:
            os.unlink(path)

    def test_load_tts_section(self):
        path = self._write_yaml({
            "tts": {
                "provider": "elevenlabs",
                "model": "custom-model",
                "voice": "alloy",
                "elevenlabs_voice_id": "abc123",
                "elevenlabs_model": "eleven_v3",
            }
        })
        try:
            cfg = load_config(path)
            assert cfg.tts.provider == "elevenlabs"
            assert cfg.tts.model == "custom-model"
            assert cfg.tts.voice == "alloy"
            assert cfg.tts.elevenlabs_voice_id == "abc123"
            assert cfg.tts.elevenlabs_model == "eleven_v3"
        finally:
            os.unlink(path)

    def test_load_llm_section(self):
        path = self._write_yaml({
            "llm": {"provider": "anthropic", "model": "claude-3-5-sonnet", "temperature": 0.3}
        })
        try:
            cfg = load_config(path)
            assert cfg.llm.provider == "anthropic"
            assert cfg.llm.model == "claude-3-5-sonnet"
            assert cfg.llm.temperature == pytest.approx(0.3)
        finally:
            os.unlink(path)

    def test_load_vad_section(self):
        path = self._write_yaml({
            "vad": {"threshold": 0.8, "min_silence_ms": 400, "min_speech_ms": 100}
        })
        try:
            cfg = load_config(path)
            assert cfg.vad.threshold == pytest.approx(0.8)
            assert cfg.vad.min_silence_ms == 400
            assert cfg.vad.min_speech_ms == 100
        finally:
            os.unlink(path)

    def test_load_turn_detection_section(self):
        path = self._write_yaml({
            "turn_detection": {"type": "silence", "allow_interruptions": False}
        })
        try:
            cfg = load_config(path)
            assert cfg.turn_detection.type == "silence"
            assert cfg.turn_detection.allow_interruptions is False
        finally:
            os.unlink(path)

    def test_load_tools_section(self):
        path = self._write_yaml({
            "tools": [
                {
                    "name": "lookup",
                    "description": "Look up a record",
                    "parameters": [
                        {"name": "id", "type": "string", "description": "Record ID", "required": True},
                        {"name": "format", "type": "string", "description": "Output format"},
                    ],
                    "webhook_url": "https://example.com/lookup",
                },
                {
                    "name": "ping",
                    "description": "Ping a host",
                },
            ]
        })
        try:
            cfg = load_config(path)
            assert len(cfg.tools) == 2

            tool0 = cfg.tools[0]
            assert tool0.name == "lookup"
            assert tool0.description == "Look up a record"
            assert tool0.webhook_url == "https://example.com/lookup"
            assert len(tool0.parameters) == 2
            assert tool0.parameters[0].name == "id"
            assert tool0.parameters[0].required is True
            assert tool0.parameters[1].name == "format"
            assert tool0.parameters[1].required is False

            tool1 = cfg.tools[1]
            assert tool1.name == "ping"
            assert tool1.parameters == []
            assert tool1.webhook_url == ""
        finally:
            os.unlink(path)

    def test_partial_agent_uses_defaults_for_missing(self):
        path = self._write_yaml({"agent": {"name": "Partial"}})
        try:
            cfg = load_config(path)
            assert cfg.agent.name == "Partial"
            assert cfg.agent.greeting == "Hello! How can I help you today?"
            assert cfg.agent.max_history == 50
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# Environment variable override
# ---------------------------------------------------------------------------

class TestEnvOverride:

    def test_agent_config_env_var(self, tmp_path, monkeypatch):
        config_file = tmp_path / "custom.yaml"
        config_file.write_text(yaml.dump({"agent": {"name": "EnvBot"}}))
        monkeypatch.setenv("AGENT_CONFIG", str(config_file))
        cfg = load_config()
        assert cfg.agent.name == "EnvBot"


# ---------------------------------------------------------------------------
# Full round-trip with the default.yaml shipped in the repo
# ---------------------------------------------------------------------------

class TestDefaultYAML:

    def test_load_default_yaml(self):
        default_path = Path(__file__).parent.parent / "configs" / "default.yaml"
        if not default_path.exists():
            pytest.skip("default.yaml not present")
        cfg = load_config(str(default_path))
        assert cfg.agent.name == "Voice Assistant"
        assert cfg.stt.provider == "deepgram"
        assert cfg.tts.provider == "openai"
        assert cfg.llm.provider == "openai"
        assert len(cfg.tools) >= 3
        tool_names = [t.name for t in cfg.tools]
        assert "get_weather" in tool_names
        assert "search_web" in tool_names
        assert "set_reminder" in tool_names
