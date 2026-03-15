"""Emotional intelligence module for the voice agent.

Provides keyword-based emotion detection from transcribed speech, rolling-window
emotion state tracking for stability, and dynamic system-prompt augmentation so
the LLM can adapt its tone to the user's emotional state.
"""
from collections import Counter
from dataclasses import dataclass, field

EMOTION_KEYWORDS: dict[str, list[str]] = {
    "frustrated": [
        "frustrated",
        "annoying",
        "annoyed",
        "ugh",
        "terrible",
        "horrible",
        "worst",
        "useless",
        "stupid",
        "broken",
        "doesn't work",
        "not working",
        "impossible",
    ],
    "confused": [
        "confused",
        "don't understand",
        "what do you mean",
        "huh",
        "unclear",
        "makes no sense",
        "lost",
        "help me understand",
    ],
    "happy": [
        "great",
        "awesome",
        "amazing",
        "wonderful",
        "fantastic",
        "love",
        "excellent",
        "perfect",
        "thank you",
        "thanks",
        "cool",
        "nice",
        "brilliant",
    ],
    "sad": [
        "sad",
        "depressed",
        "unhappy",
        "unfortunate",
        "sorry",
        "disappointed",
        "miss",
        "lonely",
        "heartbroken",
    ],
    "angry": [
        "angry",
        "furious",
        "outraged",
        "unacceptable",
        "ridiculous",
        "absurd",
        "demand",
        "immediately",
        "right now",
    ],
    "anxious": [
        "worried",
        "anxious",
        "nervous",
        "scared",
        "afraid",
        "concern",
        "stress",
        "overwhelmed",
        "panic",
    ],
    "excited": [
        "excited",
        "can't wait",
        "thrilled",
        "pumped",
        "stoked",
        "looking forward",
        "eager",
    ],
}


@dataclass
class EmotionState:
    """Tracks the user's emotional state over a rolling window of observations."""

    current_emotion: str = "neutral"
    confidence: float = 0.0
    emotion_history: list[str] = field(default_factory=list)
    # Rolling window of last N emotions for stability
    window_size: int = 5

    def update(self, new_emotion: str, confidence: float) -> None:
        """Update the emotion state with a new observation.

        Only updates when the detection confidence exceeds a minimum threshold
        of 0.3, filtering out low-signal detections. The current emotion is
        determined by majority vote over the rolling window for stability.
        """
        if confidence > 0.3:  # Only update if confidence is meaningful
            self.emotion_history.append(new_emotion)
            if len(self.emotion_history) > self.window_size:
                self.emotion_history = self.emotion_history[-self.window_size :]
            # Use most frequent emotion in window for stability
            if self.emotion_history:
                counts = Counter(self.emotion_history)
                self.current_emotion = counts.most_common(1)[0][0]
                self.confidence = confidence


def detect_emotion(text: str) -> tuple[str, float]:
    """Detect emotion from text using keyword matching.

    Scans the input text for known emotion keywords. Multi-word keywords
    receive proportionally higher weight. Returns the highest-scoring
    emotion, or ``("neutral", 0.8)`` when no keywords match.

    Args:
        text: The user's transcribed speech.

    Returns:
        A ``(emotion, confidence)`` tuple where *emotion* is one of the
        keys in ``EMOTION_KEYWORDS`` or ``"neutral"``, and *confidence*
        is a float between 0 and 1.
    """
    text_lower = text.lower()
    scores: dict[str, float] = {}

    for emotion, keywords in EMOTION_KEYWORDS.items():
        score = 0.0
        for keyword in keywords:
            if keyword in text_lower:
                # Longer keywords get higher weight
                score += len(keyword.split()) * 0.2
        if score > 0:
            scores[emotion] = min(score, 1.0)

    if not scores:
        return "neutral", 0.8

    best_emotion = max(scores, key=lambda k: scores[k])
    return best_emotion, scores[best_emotion]


def get_emotion_prompt_addition(emotion: str, adaptive_prompts: dict[str, str]) -> str:
    """Get additional system prompt based on detected emotion.

    If the caller supplies a custom prompt for the emotion via
    *adaptive_prompts*, that is used. Otherwise a sensible built-in
    default is returned. Returns an empty string for unrecognised or
    neutral emotions.

    Args:
        emotion: The detected emotion label (e.g. ``"frustrated"``).
        adaptive_prompts: Mapping of emotion names to custom prompt text,
            typically loaded from the YAML configuration.

    Returns:
        A string to append to the base system prompt, or ``""`` if no
        adaptation is needed.
    """
    if emotion in adaptive_prompts:
        return f"\n\n[Emotional context: {adaptive_prompts[emotion]}]"

    # Default prompts if not configured
    defaults = {
        "frustrated": (
            "\n\n[The user seems frustrated. Be extra patient, acknowledge "
            "their frustration, and provide clear solutions.]"
        ),
        "confused": (
            "\n\n[The user seems confused. Simplify your explanations and "
            "check for understanding.]"
        ),
        "happy": (
            "\n\n[The user is in a good mood. Match their positive energy "
            "while staying helpful.]"
        ),
        "sad": "\n\n[The user seems sad. Be warm, empathetic, and supportive.]",
        "angry": (
            "\n\n[The user seems upset. Stay calm, acknowledge their feelings, "
            "and focus on resolution.]"
        ),
        "anxious": (
            "\n\n[The user seems anxious. Be reassuring and provide clear, "
            "structured information.]"
        ),
        "excited": (
            "\n\n[The user is excited. Share in their enthusiasm while keeping "
            "responses focused.]"
        ),
    }
    return defaults.get(emotion, "")
