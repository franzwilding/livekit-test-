"""Tests for the main agent module.

These tests verify the factory functions and VoiceAssistant construction
without requiring actual LiveKit credentials or network access.
"""
import os
import tempfile

import pytest
import yaml
from unittest.mock import patch, MagicMock

from src.config import Config, load_config, STTSettings, TTSSettings, LLMSettings, TurnDetectionSettings


# ---------------------------------------------------------------------------
# Factory function tests (mocked plugin constructors)
# ---------------------------------------------------------------------------

class TestCreateSTT:
    """Test the STT factory function."""

    def test_deepgram_provider(self):
        with patch("src.agent.deepgram") as mock_dg:
            from src.agent import create_stt

            cfg = Config()
            cfg.stt = STTSettings(provider="deepgram", model="nova-3", language="multi")
            create_stt(cfg)
            mock_dg.STT.assert_called_once_with(model="nova-3", language="multi")

    def test_openai_provider(self):
        with patch("src.agent.openai") as mock_oai:
            from src.agent import create_stt

            cfg = Config()
            cfg.stt = STTSettings(provider="openai", model="whisper-1", language="en")
            create_stt(cfg)
            mock_oai.STT.assert_called_once_with(model="whisper-1", language="en")

    def test_unknown_provider_raises(self):
        from src.agent import create_stt

        cfg = Config()
        cfg.stt = STTSettings(provider="unknown")
        with pytest.raises(ValueError, match="Unknown STT provider"):
            create_stt(cfg)


class TestCreateTTS:
    """Test the TTS factory function."""

    def test_openai_provider(self):
        with patch("src.agent.openai") as mock_oai:
            from src.agent import create_tts

            cfg = Config()
            cfg.tts = TTSSettings(provider="openai", model="gpt-4o-mini-tts", voice="coral")
            create_tts(cfg)
            mock_oai.TTS.assert_called_once_with(model="gpt-4o-mini-tts", voice="coral")

    def test_elevenlabs_provider_with_voice_name(self):
        with patch("src.agent.elevenlabs") as mock_el:
            from src.agent import create_tts

            cfg = Config()
            cfg.tts = TTSSettings(
                provider="elevenlabs",
                voice="Rachel",
                elevenlabs_voice_id="",
                elevenlabs_model="eleven_turbo_v2_5",
            )
            create_tts(cfg)
            mock_el.TTS.assert_called_once()
            call_kwargs = mock_el.TTS.call_args
            assert call_kwargs.kwargs["model"] == "eleven_turbo_v2_5"

    def test_elevenlabs_provider_with_voice_id(self):
        with patch("src.agent.elevenlabs") as mock_el:
            from src.agent import create_tts

            cfg = Config()
            cfg.tts = TTSSettings(
                provider="elevenlabs",
                voice="Rachel",
                elevenlabs_voice_id="abc123",
                elevenlabs_model="eleven_turbo_v2_5",
            )
            create_tts(cfg)
            mock_el.TTS.assert_called_once()
            # The Voice should be created with id= when voice_id is provided
            mock_el.Voice.assert_called_with(id="abc123")

    def test_unknown_provider_raises(self):
        from src.agent import create_tts

        cfg = Config()
        cfg.tts = TTSSettings(provider="unknown")
        with pytest.raises(ValueError, match="Unknown TTS provider"):
            create_tts(cfg)


class TestCreateLLM:
    """Test the LLM factory function."""

    def test_openai_provider(self):
        with patch("src.agent.openai") as mock_oai:
            from src.agent import create_llm

            cfg = Config()
            cfg.llm = LLMSettings(provider="openai", model="gpt-4o", temperature=0.7)
            create_llm(cfg)
            mock_oai.LLM.assert_called_once_with(model="gpt-4o", temperature=0.7)

    def test_anthropic_provider(self):
        with patch("src.agent.anthropic_plugin") as mock_ant:
            from src.agent import create_llm

            cfg = Config()
            cfg.llm = LLMSettings(provider="anthropic", model="claude-3-5-sonnet", temperature=0.5)
            create_llm(cfg)
            mock_ant.LLM.assert_called_once_with(model="claude-3-5-sonnet", temperature=0.5)

    def test_unknown_provider_raises(self):
        from src.agent import create_llm

        cfg = Config()
        cfg.llm = LLMSettings(provider="unknown")
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            create_llm(cfg)


class TestCreateTurnDetector:
    """Test the turn detector factory function."""

    def test_multilingual_returns_model(self):
        with patch("src.agent.MultilingualModel") as mock_mm:
            from src.agent import create_turn_detector

            cfg = Config()
            cfg.turn_detection = TurnDetectionSettings(type="multilingual")
            result = create_turn_detector(cfg)
            mock_mm.assert_called_once()

    def test_silence_returns_none(self):
        from src.agent import create_turn_detector

        cfg = Config()
        cfg.turn_detection = TurnDetectionSettings(type="silence")
        result = create_turn_detector(cfg)
        assert result is None


# ---------------------------------------------------------------------------
# VoiceAssistant construction
# ---------------------------------------------------------------------------

class TestVoiceAssistant:
    """Test VoiceAssistant instantiation and configuration."""

    def test_creates_with_default_config(self):
        with patch("src.agent.Agent.__init__", return_value=None):
            from src.agent import VoiceAssistant

            cfg = Config()
            agent = VoiceAssistant(cfg)
            assert agent._cfg is cfg
            assert agent._emotion_state is not None
            assert agent._emotion_state.current_emotion == "neutral"

    def test_emotion_disabled_no_extra_instructions(self):
        with patch("src.agent.Agent.__init__", return_value=None) as mock_init:
            from src.agent import VoiceAssistant
            from src.config import EmotionSettings

            cfg = Config()
            cfg.emotion = EmotionSettings(enabled=False)
            cfg.agent.system_prompt = "Be helpful."
            agent = VoiceAssistant(cfg)
            # The Agent.__init__ should have been called with instructions
            call_kwargs = mock_init.call_args
            instructions = call_kwargs.kwargs.get("instructions", "")
            assert "emotional intelligence" not in instructions.lower()

    def test_emotion_enabled_adds_instructions(self):
        with patch("src.agent.Agent.__init__", return_value=None) as mock_init:
            from src.agent import VoiceAssistant
            from src.config import EmotionSettings

            cfg = Config()
            cfg.emotion = EmotionSettings(enabled=True)
            cfg.agent.system_prompt = "Be helpful."
            agent = VoiceAssistant(cfg)
            call_kwargs = mock_init.call_args
            instructions = call_kwargs.kwargs.get("instructions", "")
            assert "emotional intelligence" in instructions.lower()

    def test_hooks_initialized_with_adaptive_prompts(self):
        with patch("src.agent.Agent.__init__", return_value=None):
            from src.agent import VoiceAssistant
            from src.config import EmotionSettings

            custom_prompts = {"happy": "Be very cheerful!"}
            cfg = Config()
            cfg.emotion = EmotionSettings(enabled=True, adaptive_prompts=custom_prompts)
            agent = VoiceAssistant(cfg)
            assert agent._hooks.adaptive_prompts == custom_prompts


# ---------------------------------------------------------------------------
# Integration: config -> agent wiring
# ---------------------------------------------------------------------------

class TestConfigToAgentWiring:
    """End-to-end tests from YAML config to agent factory outputs."""

    def _write_yaml(self, data: dict) -> str:
        fd, path = tempfile.mkstemp(suffix=".yaml")
        with os.fdopen(fd, "w") as f:
            yaml.dump(data, f)
        return path

    def test_full_config_creates_all_providers(self):
        """Verify a complete config can drive all factory functions."""
        path = self._write_yaml({
            "agent": {"name": "IntegrationBot"},
            "stt": {"provider": "deepgram", "model": "nova-3", "language": "en"},
            "tts": {"provider": "openai", "model": "gpt-4o-mini-tts", "voice": "alloy"},
            "llm": {"provider": "openai", "model": "gpt-4o", "temperature": 0.5},
            "turn_detection": {"type": "silence"},
        })
        try:
            cfg = load_config(path)
            assert cfg.agent.name == "IntegrationBot"

            with patch("src.agent.deepgram") as mock_dg:
                from src.agent import create_stt
                create_stt(cfg)
                mock_dg.STT.assert_called_once()

            with patch("src.agent.openai") as mock_oai:
                from src.agent import create_tts
                create_tts(cfg)
                mock_oai.TTS.assert_called_once()

            with patch("src.agent.openai") as mock_oai:
                from src.agent import create_llm
                create_llm(cfg)
                mock_oai.LLM.assert_called_once()

            from src.agent import create_turn_detector
            assert create_turn_detector(cfg) is None  # silence type
        finally:
            os.unlink(path)

    def test_anthropic_llm_config(self):
        path = self._write_yaml({
            "llm": {"provider": "anthropic", "model": "claude-3-5-sonnet", "temperature": 0.3}
        })
        try:
            cfg = load_config(path)
            with patch("src.agent.anthropic_plugin") as mock_ant:
                from src.agent import create_llm
                create_llm(cfg)
                mock_ant.LLM.assert_called_once_with(
                    model="claude-3-5-sonnet", temperature=0.3
                )
        finally:
            os.unlink(path)
