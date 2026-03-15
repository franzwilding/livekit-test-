"""Lifecycle hooks for the voice agent pipeline.

Provides the ``AgentHooks`` class which bridges the emotion detection system
with the LiveKit agent pipeline, updating emotion state on each user utterance
and injecting emotion-aware context into the LLM system prompt.
"""
import logging

from src.emotion import EmotionState, detect_emotion, get_emotion_prompt_addition

logger = logging.getLogger("hooks")


class AgentHooks:
    """Manages lifecycle hooks for emotion-aware responses.

    Attributes:
        emotion_state: The shared ``EmotionState`` instance tracking the
            user's emotional trajectory.
        adaptive_prompts: Mapping of emotion names to custom prompt
            additions, typically sourced from YAML configuration.
    """

    def __init__(self, emotion_state: EmotionState, adaptive_prompts: dict[str, str]) -> None:
        self.emotion_state = emotion_state
        self.adaptive_prompts = adaptive_prompts

    def on_user_speech(self, text: str) -> None:
        """Called when user speech is transcribed. Updates emotion state.

        Args:
            text: The transcribed user utterance.
        """
        emotion, confidence = detect_emotion(text)
        self.emotion_state.update(emotion, confidence)
        logger.info(f"Detected emotion: {emotion} (confidence: {confidence:.2f})")

    def get_dynamic_instructions(self, base_instructions: str) -> str:
        """Get instructions with emotion context appended.

        When the current emotion is ``"neutral"`` the base instructions are
        returned unchanged. Otherwise the appropriate emotion-adaptive
        prompt is appended.

        Args:
            base_instructions: The original system prompt.

        Returns:
            The augmented system prompt string.
        """
        if self.emotion_state.current_emotion == "neutral":
            return base_instructions

        addition = get_emotion_prompt_addition(
            self.emotion_state.current_emotion,
            self.adaptive_prompts,
        )
        return base_instructions + addition
