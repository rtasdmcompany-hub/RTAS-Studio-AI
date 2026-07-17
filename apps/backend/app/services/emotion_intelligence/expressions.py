"""Facial Expression Engine — eyes, brows, mouth, blink, head tilt."""

from __future__ import annotations

from typing import Any

from app.services.emotion_intelligence.library import get_emotion_spec, resolve_emotion
from app.services.emotion_intelligence.models import FacialExpression


def generate_facial_expression(
    emotion: str,
    *,
    intensity: float | None = None,
) -> FacialExpression:
    emo = resolve_emotion(emotion)
    spec = get_emotion_spec(emo)
    base_intensity = float(intensity if intensity is not None else spec.get("arousal", 0.5))
    base_intensity = max(0.1, min(1.0, base_intensity))
    smile = float(spec.get("smile", 0.2)) * base_intensity

    eye_open = 0.55 + (0.25 if emo in ("surprised", "shocked", "fear") else 0.0)
    if emo in ("tired", "sad", "crying"):
        eye_open = 0.35

    brow_raise = 0.7 if emo in ("surprised", "shocked", "confused", "thinking") else 0.2
    brow_furrow = 0.75 if emo in ("angry", "serious", "confused") else 0.1

    mouth_shape = "smile" if smile >= 0.45 else "neutral"
    if emo in ("angry", "serious"):
        mouth_shape = "tight"
    elif emo in ("shocked", "surprised", "fear"):
        mouth_shape = "open"
    elif emo in ("sad", "crying"):
        mouth_shape = "downturned"
    elif emo == "laughing":
        mouth_shape = "wide_open_smile"

    score = 100.0 - abs(0.5 - base_intensity) * 10.0
    if emo in ("happy", "smiling", "laughing") and smile < 0.3:
        score -= 15
    score = max(0.0, min(100.0, score))

    return FacialExpression(
        emotion=emo,
        eye_movement={
            "gaze": "camera" if emo in ("happy", "romantic", "motivational") else "environment",
            "saccade_rate": round(0.2 + base_intensity * 0.3, 3),
            "openness": round(eye_open, 3),
        },
        eyebrow_movement={
            "raise": round(brow_raise * base_intensity, 3),
            "furrow": round(brow_furrow * base_intensity, 3),
        },
        mouth_expression={"shape": mouth_shape, "openness": round(0.2 + smile * 0.5, 3)},
        smile_intensity=round(smile, 3),
        lip_movement={
            "compression": round(0.5 if mouth_shape == "tight" else 0.15, 3),
            "speech_ready": emo in ("motivational", "serious", "angry", "emotional"),
        },
        cheek_movement={"raise": round(smile * 0.8, 3)},
        forehead_movement={
            "wrinkle": round(0.6 * base_intensity if emo in ("worried", "nervous", "thinking", "confused") else 0.1, 3)
        },
        head_tilt={
            "roll_deg": round((-6 if emo == "confused" else 3 if emo == "curious" else 0) * base_intensity, 2),
            "pitch_deg": round((-4 if emo in ("sad", "crying") else 2 if emo == "proud" else 0), 2),
        },
        eye_contact={
            "strength": round(0.8 if emo in ("serious", "romantic", "motivational") else 0.5, 3),
            "break_rate": round(0.3 if emo in ("nervous", "shy", "sad") else 0.1, 3),
        },
        blink_timing={
            "rate_hz": round(0.25 + (0.2 if emo in ("nervous", "fear") else 0.0), 3),
            "duration_ms": 120 if emo != "surprised" else 80,
        },
        expression_score=round(score, 2),
        face_lock_respected=True,
    )
