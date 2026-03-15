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
            mock_el.Voice.assert_called_with(id="abc123")

    def test_unknown_provider_raises(self):
        from src.agent import create_tts

        cfg = Config()
        cfg.tts = TTSSettings(provider="unknown")
        with pytest.raises(ValueError, match="Unknown TTS provider"):
            create_tts(cfg)


class TestCreateLLM:

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

    def test_multilingual_returns_model(self):
        with patch("src.agent.MultilingualModel") as mock_mm:
            from src.agent import create_turn_detector

            cfg = Config()
            cfg.turn_detection = TurnDetectionSettings(type="multilingual")
            create_turn_detector(cfg)
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

    def test_creates_with_default_config(self):
        with patch("src.agent.Agent.__init__", return_value=None):
            from src.agent import VoiceAssistant

            cfg = Config()
            agent = VoiceAssistant(cfg)
            assert agent._cfg is cfg

    def test_system_prompt_passed_to_agent(self):
        with patch("src.agent.Agent.__init__", return_value=None) as mock_init:
            from src.agent import VoiceAssistant

            cfg = Config()
            cfg.agent.system_prompt = "Be helpful and concise."
            VoiceAssistant(cfg)
            call_kwargs = mock_init.call_args
            assert call_kwargs.kwargs["instructions"] == "Be helpful and concise."

    def test_messenger_property_when_set(self):
        with patch("src.agent.Agent.__init__", return_value=None):
            from src.agent import VoiceAssistant
            messenger = MagicMock()
            cfg = Config()
            agent = VoiceAssistant(cfg, messenger=messenger)
            assert agent.messenger is messenger

    def test_messenger_none_by_default(self):
        with patch("src.agent.Agent.__init__", return_value=None):
            from src.agent import VoiceAssistant
            cfg = Config()
            agent = VoiceAssistant(cfg)
            assert agent.messenger is None


# ---------------------------------------------------------------------------
# Integration: config -> agent wiring
# ---------------------------------------------------------------------------

class TestConfigToAgentWiring:

    def _write_yaml(self, data: dict) -> str:
        fd, path = tempfile.mkstemp(suffix=".yaml")
        with os.fdopen(fd, "w") as f:
            yaml.dump(data, f)
        return path

    def test_full_config_creates_all_providers(self):
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
            assert create_turn_detector(cfg) is None
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
