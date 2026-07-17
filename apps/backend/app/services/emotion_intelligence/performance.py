"""Body Performance Engine — sync emotion with gestures and posture."""

from __future__ import annotations

from app.services.emotion_intelligence.library import get_emotion_spec, resolve_emotion
from app.services.emotion_intelligence.models import BodyPerformance


def generate_body_performance(
    emotion: str,
    *,
    intensity: float | None = None,
) -> BodyPerformance:
    emo = resolve_emotion(emotion)
    spec = get_emotion_spec(emo)
    energy = float(intensity if intensity is not None else spec.get("energy", 0.5))
    energy = max(0.1, min(1.0, energy))

    hand_map = {
        "happy": [{"gesture": "open_palm", "amp": 0.6}],
        "excited": [{"gesture": "open_palm", "amp": 0.85}, {"gesture": "wave", "amp": 0.5}],
        "angry": [{"gesture": "fist", "amp": 0.8}],
        "motivational": [{"gesture": "point", "amp": 0.7}],
        "thinking": [{"gesture": "chin_touch", "amp": 0.45}],
        "nervous": [{"gesture": "fidget", "amp": 0.55}],
        "romantic": [{"gesture": "soft_reach", "amp": 0.4}],
        "crying": [{"gesture": "cover_face", "amp": 0.5}],
        "laughing": [{"gesture": "open_palm", "amp": 0.65}],
    }
    hands = hand_map.get(emo, [{"gesture": "neutral", "amp": 0.3}])
    for h in hands:
        h["amp"] = round(float(h["amp"]) * energy, 3)

    walking = "light_bounce" if emo in ("happy", "excited") else "heavy" if emo in ("sad", "angry") else "natural"
    standing = "open_chest" if emo in ("proud", "motivational") else "closed" if emo in ("fear", "nervous") else "neutral"
    sitting = "lean_forward" if emo in ("interested", "serious", "thinking") else "slumped" if emo == "sad" else "upright"

    return BodyPerformance(
        emotion=emo,
        hand_gestures=hands,
        walking_style=walking,
        standing_pose=standing,
        sitting_pose=sitting,
        head_movement={
            "nod": emo in ("motivational", "happy", "proud"),
            "shake": emo in ("confused", "nervous"),
            "amp": round(0.2 + energy * 0.3, 3),
        },
        shoulder_movement={
            "raise": round(0.5 * energy if emo in ("shrug", "confused", "nervous") else 0.1, 3),
            "tension": round(0.7 * energy if emo in ("angry", "fear", "nervous") else 0.2, 3),
        },
        body_balance={
            "center": "forward" if emo in ("excited", "angry", "motivational") else "back" if emo in ("fear", "sad") else "center",
            "sway": round(0.15 * energy, 3),
        },
        natural_breathing={
            "rate": round(0.25 + energy * 0.35, 3),
            "depth": round(0.4 + (0.3 if emo in ("fear", "excited") else 0.1), 3),
            "preserve_body": True,
        },
        intensity=round(energy, 3),
    )
