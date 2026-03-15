"""Tests for the emotional intelligence module."""
import pytest

from src.emotion import (
    EMOTION_KEYWORDS,
    EmotionState,
    detect_emotion,
    get_emotion_prompt_addition,
)


# ---------------------------------------------------------------------------
# detect_emotion
# ---------------------------------------------------------------------------

class TestDetectEmotion:
    """Verify keyword-based emotion detection."""

    def test_neutral_when_no_keywords(self):
        emotion, confidence = detect_emotion("Tell me about the Eiffel Tower.")
        assert emotion == "neutral"
        assert confidence == pytest.approx(0.8)

    def test_detects_happy(self):
        emotion, _ = detect_emotion("That's awesome, thank you so much!")
        assert emotion == "happy"

    def test_detects_frustrated(self):
        emotion, _ = detect_emotion("This is so annoying, it doesn't work!")
        assert emotion == "frustrated"

    def test_detects_confused(self):
        emotion, _ = detect_emotion("I don't understand, what do you mean?")
        assert emotion == "confused"

    def test_detects_sad(self):
        emotion, _ = detect_emotion("I feel so sad and lonely today.")
        assert emotion == "sad"

    def test_detects_angry(self):
        emotion, _ = detect_emotion("This is absolutely unacceptable and ridiculous!")
        assert emotion == "angry"

    def test_detects_anxious(self):
        emotion, _ = detect_emotion("I'm really worried and stressed about this.")
        assert emotion == "anxious"

    def test_detects_excited(self):
        emotion, _ = detect_emotion("I'm so excited, I can't wait!")
        assert emotion == "excited"

    def test_case_insensitive(self):
        emotion, _ = detect_emotion("AWESOME! FANTASTIC! AMAZING!")
        assert emotion == "happy"

    def test_multi_word_keywords_score_higher(self):
        """Multi-word keywords like 'don't understand' should get extra weight."""
        emotion, confidence = detect_emotion("I don't understand this at all.")
        assert emotion == "confused"
        assert confidence > 0.3

    def test_confidence_capped_at_one(self):
        # Load up a message with many happy keywords
        text = "great awesome amazing wonderful fantastic love excellent perfect brilliant cool nice"
        _, confidence = detect_emotion(text)
        assert confidence <= 1.0

    def test_empty_string_is_neutral(self):
        emotion, confidence = detect_emotion("")
        assert emotion == "neutral"
        assert confidence == pytest.approx(0.8)

    def test_competing_emotions_picks_strongest(self):
        """When multiple emotions match, the strongest score wins."""
        # 'frustrated' keywords: annoying, terrible, horrible, worst
        # vs 'happy' keywords: great
        text = "This is terrible, horrible, the worst, and annoying. But great I guess."
        emotion, _ = detect_emotion(text)
        assert emotion == "frustrated"


# ---------------------------------------------------------------------------
# EmotionState
# ---------------------------------------------------------------------------

class TestEmotionState:
    """Test the rolling-window emotion state tracker."""

    def test_initial_state_is_neutral(self):
        state = EmotionState()
        assert state.current_emotion == "neutral"
        assert state.confidence == 0.0
        assert state.emotion_history == []

    def test_update_with_high_confidence(self):
        state = EmotionState()
        state.update("happy", 0.6)
        assert state.current_emotion == "happy"
        assert state.confidence == pytest.approx(0.6)
        assert state.emotion_history == ["happy"]

    def test_update_ignores_low_confidence(self):
        state = EmotionState()
        state.update("angry", 0.2)
        assert state.current_emotion == "neutral"
        assert state.emotion_history == []

    def test_majority_vote_in_window(self):
        state = EmotionState(window_size=5)
        state.update("happy", 0.5)
        state.update("happy", 0.5)
        state.update("sad", 0.5)
        assert state.current_emotion == "happy"

    def test_window_truncation(self):
        state = EmotionState(window_size=3)
        state.update("happy", 0.5)
        state.update("happy", 0.5)
        state.update("happy", 0.5)
        state.update("sad", 0.5)
        state.update("sad", 0.5)
        # Window: [happy, sad, sad] -> sad wins
        assert state.current_emotion == "sad"
        assert len(state.emotion_history) == 3

    def test_single_update_becomes_current(self):
        state = EmotionState(window_size=5)
        state.update("excited", 0.9)
        assert state.current_emotion == "excited"

    def test_confidence_threshold_boundary(self):
        state = EmotionState()
        # Exactly 0.3 should NOT trigger update (> 0.3 required)
        state.update("angry", 0.3)
        assert state.current_emotion == "neutral"
        # Just above threshold
        state.update("angry", 0.31)
        assert state.current_emotion == "angry"


# ---------------------------------------------------------------------------
# get_emotion_prompt_addition
# ---------------------------------------------------------------------------

class TestGetEmotionPromptAddition:
    """Test adaptive prompt generation."""

    def test_custom_prompt_used_when_available(self):
        prompts = {"happy": "Be cheerful!"}
        result = get_emotion_prompt_addition("happy", prompts)
        assert "Be cheerful!" in result
        assert "[Emotional context:" in result

    def test_default_prompt_for_known_emotion(self):
        result = get_emotion_prompt_addition("frustrated", {})
        assert "frustrated" in result.lower()
        assert len(result) > 0

    def test_all_default_emotions_have_prompts(self):
        for emotion in ["frustrated", "confused", "happy", "sad", "angry", "anxious", "excited"]:
            result = get_emotion_prompt_addition(emotion, {})
            assert len(result) > 0, f"No default prompt for {emotion}"

    def test_unknown_emotion_returns_empty(self):
        result = get_emotion_prompt_addition("bored", {})
        assert result == ""

    def test_neutral_returns_empty(self):
        result = get_emotion_prompt_addition("neutral", {})
        assert result == ""

    def test_custom_prompt_overrides_default(self):
        custom = {"frustrated": "Custom frustration message."}
        result = get_emotion_prompt_addition("frustrated", custom)
        assert "Custom frustration message." in result
        # Should NOT contain the default text
        assert "Be extra patient" not in result


# ---------------------------------------------------------------------------
# EMOTION_KEYWORDS sanity checks
# ---------------------------------------------------------------------------

class TestEmotionKeywords:
    """Verify the keyword dictionary is well-formed."""

    def test_all_emotions_have_keywords(self):
        expected = {"frustrated", "confused", "happy", "sad", "angry", "anxious", "excited"}
        assert expected.issubset(set(EMOTION_KEYWORDS.keys()))

    def test_keywords_are_lowercase(self):
        for emotion, keywords in EMOTION_KEYWORDS.items():
            for kw in keywords:
                assert kw == kw.lower(), f"Keyword '{kw}' for {emotion} is not lowercase"

    def test_no_empty_keyword_lists(self):
        for emotion, keywords in EMOTION_KEYWORDS.items():
            assert len(keywords) > 0, f"Emotion {emotion} has no keywords"
