"""Emotion → facial expression parameters for talking avatar."""

from __future__ import annotations

from typing import Any

# emotion -> (smile, brow_raise, intensity)
_EMOTION_MAP: dict[str, tuple[float, float, float]] = {
    "neutral": (0.15, 0.1, 0.35),
    "calm": (0.2, 0.1, 0.3),
    "happy": (0.75, 0.25, 0.7),
    "joy": (0.85, 0.3, 0.8),
    "sad": (0.05, 0.15, 0.55),
    "somber": (0.08, 0.12, 0.5),
    "lonely": (0.05, 0.1, 0.45),
    "angry": (0.05, 0.55, 0.75),
    "fear": (0.1, 0.65, 0.7),
    "surprise": (0.25, 0.8, 0.75),
    "hope": (0.45, 0.3, 0.55),
    "confident": (0.4, 0.2, 0.6),
    "professional": (0.25, 0.15, 0.45),
}


def resolve_emotion(
    *,
    prompt: str,
    audio_director: dict[str, Any] | None = None,
    director_plan: dict[str, Any] | None = None,
    emotion_hint: str | None = None,
) -> str:
    if emotion_hint:
        return emotion_hint.strip().lower()
    det = (audio_director or {}).get("detection") or {}
    if isinstance(det, dict) and det.get("emotion"):
        return str(det["emotion"]).lower()
    pacing = (director_plan or {}).get("emotional_pacing") or []
    if pacing and isinstance(pacing[0], str):
        return pacing[0].lower()
    text = (prompt or "").lower()
    for key in _EMOTION_MAP:
        if key in text:
            return key
    return "neutral"


def emotion_params(emotion: str) -> tuple[float, float, float]:
    return _EMOTION_MAP.get(emotion.lower(), _EMOTION_MAP["neutral"])
