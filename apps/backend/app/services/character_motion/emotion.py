"""Emotion-based movement adaptation."""

from __future__ import annotations

from typing import Any

from app.services.character_motion.models import EmotionTone

_EMOTION_BIAS: dict[str, dict[str, float]] = {
    "happy": {"stride": 0.08, "cadence": 0.1, "arm_swing": 0.15, "gesture_amp": 0.15, "spine_lean": 0.0, "head_yaw": 0.05, "blink": 0.05},
    "sad": {"stride": -0.12, "cadence": -0.15, "arm_swing": -0.1, "gesture_amp": -0.1, "spine_lean": 0.12, "head_pitch": 0.08, "blink": 0.1},
    "angry": {"stride": 0.12, "cadence": 0.18, "arm_swing": 0.2, "gesture_amp": 0.25, "spine_lean": 0.05, "head_yaw": 0.08},
    "romantic": {"stride": -0.05, "cadence": -0.05, "arm_swing": 0.05, "gesture_amp": 0.05, "spine_lean": 0.02, "head_yaw": 0.04},
    "serious": {"stride": 0.0, "cadence": -0.05, "arm_swing": -0.05, "gesture_amp": 0.0, "spine_lean": 0.0},
    "motivational": {"stride": 0.1, "cadence": 0.12, "arm_swing": 0.18, "gesture_amp": 0.2, "spine_lean": -0.02},
    "fear": {"stride": 0.05, "cadence": 0.2, "arm_swing": -0.05, "gesture_amp": 0.1, "spine_lean": 0.08, "saccade": 0.2, "blink": 0.15},
    "suspense": {"stride": -0.08, "cadence": -0.1, "arm_swing": -0.08, "gesture_amp": -0.05, "spine_lean": 0.04, "saccade": 0.15},
    "excited": {"stride": 0.15, "cadence": 0.22, "arm_swing": 0.25, "gesture_amp": 0.3, "spine_lean": -0.03, "head_yaw": 0.1},
    "calm": {"stride": 0.0, "cadence": 0.0, "arm_swing": 0.0, "gesture_amp": 0.0, "spine_lean": 0.0},
}


def resolve_emotion(emotion: str | None) -> EmotionTone:
    e = (emotion or "calm").strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {"motivate": "motivational", "scared": "fear", "tense": "suspense", "joy": "happy"}
    e = aliases.get(e, e)
    if e not in _EMOTION_BIAS:
        return "calm"
    return e  # type: ignore[return-value]


def emotion_movement_bias(emotion: str | None) -> dict[str, float]:
    key = resolve_emotion(emotion)
    return dict(_EMOTION_BIAS[key])


def emotion_payload(emotion: str | None) -> dict[str, Any]:
    key = resolve_emotion(emotion)
    return {"emotion": key, "bias": emotion_movement_bias(key)}
