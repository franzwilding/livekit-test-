"""Tests for the voice agent."""
from unittest.mock import patch, MagicMock


class TestVoiceAssistant:

    def test_system_prompt_passed(self):
        with patch("src.agent.Agent.__init__", return_value=None) as mock_init:
            from src.agent import VoiceAssistant, SYSTEM_PROMPT

            VoiceAssistant()
            mock_init.assert_called_once_with(instructions=SYSTEM_PROMPT)

    def test_messenger_property(self):
        with patch("src.agent.Agent.__init__", return_value=None):
            from src.agent import VoiceAssistant

            messenger = MagicMock()
            agent = VoiceAssistant(messenger=messenger)
            assert agent.messenger is messenger

    def test_messenger_none_by_default(self):
        with patch("src.agent.Agent.__init__", return_value=None):
            from src.agent import VoiceAssistant

            assert VoiceAssistant().messenger is None
