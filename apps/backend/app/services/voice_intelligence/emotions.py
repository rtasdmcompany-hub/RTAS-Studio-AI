"""Emotion Voice Engine — detect emotional tone per dialogue line."""

from __future__ import annotations

import re

from app.services.voice_intelligence.models import EmotionTone

_EMOTION_KEYWORDS: dict[EmotionTone, tuple[str, ...]] = {
    "happy": ("happy", "joy", "smile", "laugh", "cheer", "glad", "delight", "wonderful"),
    "sad": ("sad", "cry", "tears", "grief", "lonely", "miss you", "heartbroken", "sorrow"),
    "angry": ("angry", "furious", "rage", "hate", "damn", "idiot", "shut up", "betray"),
    "romantic": ("love", "kiss", "heart", "darling", "romance", "forever", "beloved"),
    "motivational": ("believe", "achieve", "dream", "inspire", "rise", "champion", "never give up"),
    "emotional": ("feel", "emotion", "vulnerable", "memory", "touched", "moved"),
    "fear": ("afraid", "scared", "terror", "panic", "nightmare", "danger", "help me"),
    "serious": ("must", "critical", "important", "decision", "truth", "responsibility"),
    "calm": ("calm", "peace", "breathe", "gentle", "quietly", "softly", "relax"),
    "suspense": ("wait", "listen", "shadow", "unknown", "behind you", "suddenly", "who is"),
    "excited": ("wow", "amazing", "excited", "can't wait", "incredible", "yes!", "lets go"),
}


def detect_emotion(text: str, *, default: EmotionTone = "calm") -> EmotionTone:
    lowered = (text or "").strip().lower()
    if not lowered:
        return default
    scores: dict[str, float] = {k: 0.0 for k in _EMOTION_KEYWORDS}
    for emotion, keywords in _EMOTION_KEYWORDS.items():
        for kw in keywords:
            if kw in lowered:
                scores[emotion] += 1.0 + (0.25 if kw in lowered.split() else 0.0)
    # Punctuation hints
    if "!" in text and scores["excited"] == 0 and scores["angry"] == 0:
        scores["excited"] += 0.5
    if "?" in text and scores["suspense"] == 0:
        scores["suspense"] += 0.3
    if re.search(r"\b(i love you|my love)\b", lowered):
        scores["romantic"] += 2.0
    best = max(scores.items(), key=lambda kv: kv[1])
    if best[1] <= 0:
        return default
    return best[0]  # type: ignore[return-value]


def emotion_delivery_hints(emotion: EmotionTone) -> dict[str, float | str]:
    table: dict[EmotionTone, dict[str, float | str]] = {
        "happy": {"energy": 0.8, "pitch_bias": 1.08, "pace_bias": 1.05, "style": "bright"},
        "sad": {"energy": 0.35, "pitch_bias": 0.92, "pace_bias": 0.85, "style": "soft"},
        "angry": {"energy": 0.95, "pitch_bias": 1.12, "pace_bias": 1.15, "style": "harsh"},
        "romantic": {"energy": 0.55, "pitch_bias": 0.98, "pace_bias": 0.9, "style": "warm"},
        "motivational": {"energy": 0.85, "pitch_bias": 1.05, "pace_bias": 1.08, "style": "powerful"},
        "emotional": {"energy": 0.6, "pitch_bias": 0.97, "pace_bias": 0.88, "style": "expressive"},
        "fear": {"energy": 0.7, "pitch_bias": 1.1, "pace_bias": 1.12, "style": "tense"},
        "serious": {"energy": 0.5, "pitch_bias": 0.95, "pace_bias": 0.92, "style": "firm"},
        "calm": {"energy": 0.4, "pitch_bias": 1.0, "pace_bias": 0.95, "style": "even"},
        "suspense": {"energy": 0.65, "pitch_bias": 0.96, "pace_bias": 0.8, "style": "hushed"},
        "excited": {"energy": 0.9, "pitch_bias": 1.15, "pace_bias": 1.2, "style": "dynamic"},
    }
    return dict(table.get(emotion, table["calm"]))
