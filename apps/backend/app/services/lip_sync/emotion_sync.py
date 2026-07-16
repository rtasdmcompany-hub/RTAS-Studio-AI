"""Emotion sync — modulate mouth shapes by emotional performance."""

from __future__ import annotations

from typing import Any

from app.services.lip_sync.models import VisemeCue

# emotion -> (openness_scale, tension, confidence_boost)
_EMOTION_MOD: dict[str, tuple[float, float, float]] = {
    "neutral": (1.0, 0.0, 0.0),
    "calm": (0.95, -0.05, 0.0),
    "happy": (1.08, -0.05, 0.02),
    "joy": (1.12, -0.08, 0.03),
    "sad": (0.88, 0.1, -0.02),
    "somber": (0.9, 0.08, -0.02),
    "angry": (1.15, 0.2, 0.0),
    "fear": (1.05, 0.15, -0.03),
    "surprise": (1.18, 0.05, 0.0),
    "confident": (1.05, 0.0, 0.03),
    "professional": (1.0, 0.02, 0.02),
}


def resolve_emotion(
    *,
    emotion_hint: str | None = None,
    audio_director: dict[str, Any] | None = None,
    dialogue: str | None = None,
) -> tuple[str, float]:
    if emotion_hint:
        return emotion_hint.strip().lower(), 0.7
    det = (audio_director or {}).get("detection") or {}
    if isinstance(det, dict) and det.get("emotion"):
        return str(det["emotion"]).lower(), 0.7
    text = (dialogue or "").lower()
    for key in ("angry", "sad", "happy", "fear", "joy", "surprise", "confident"):
        if key in text:
            return key, 0.65
    return "neutral", 0.5


def apply_emotion_to_visemes(
    visemes: list[VisemeCue],
    emotion: str,
    intensity: float,
) -> list[VisemeCue]:
    scale, tension, conf = _EMOTION_MOD.get(emotion.lower(), _EMOTION_MOD["neutral"])
    # Blend toward emotion scale by intensity
    openness_scale = 1.0 + (scale - 1.0) * intensity
    out: list[VisemeCue] = []
    for v in visemes:
        openness = min(1.0, max(0.05, v.mouth_openness * openness_scale))
        # Tension slightly reduces lip width for angry/sad
        width = min(1.0, max(0.15, v.lip_width * (1.0 - tension * 0.2)))
        roundness = min(1.0, max(0.0, v.lip_round + tension * 0.05))
        out.append(
            VisemeCue(
                index=v.index,
                start_sec=v.start_sec,
                end_sec=v.end_sec,
                phoneme=v.phoneme,
                viseme=v.viseme,
                mouth_openness=round(openness, 3),
                jaw_drop=round(min(1.0, openness * 0.85), 3),
                lip_round=round(roundness, 3),
                lip_width=round(width, 3),
                emotion=emotion,
                emotion_intensity=round(intensity, 3),
                language=v.language,
                dialogue_snippet=v.dialogue_snippet,
                sync_confidence=round(min(1.0, v.sync_confidence + conf), 3),
            )
        )
    return out
