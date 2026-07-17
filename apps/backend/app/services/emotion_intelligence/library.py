"""Emotion / Expression / Performance libraries — extensible catalogs."""

from __future__ import annotations

from typing import Any

_BUILTIN_EMOTIONS: dict[str, dict[str, Any]] = {
    "happy": {"valence": 0.8, "arousal": 0.6, "smile": 0.75, "energy": 0.7},
    "sad": {"valence": -0.7, "arousal": 0.3, "smile": 0.05, "energy": 0.25},
    "angry": {"valence": -0.6, "arousal": 0.85, "smile": 0.0, "energy": 0.9},
    "romantic": {"valence": 0.65, "arousal": 0.45, "smile": 0.55, "energy": 0.5},
    "excited": {"valence": 0.85, "arousal": 0.9, "smile": 0.8, "energy": 0.95},
    "fear": {"valence": -0.75, "arousal": 0.8, "smile": 0.0, "energy": 0.7},
    "suspense": {"valence": -0.2, "arousal": 0.65, "smile": 0.1, "energy": 0.55},
    "serious": {"valence": 0.0, "arousal": 0.4, "smile": 0.05, "energy": 0.45},
    "calm": {"valence": 0.3, "arousal": 0.2, "smile": 0.25, "energy": 0.3},
    "motivational": {"valence": 0.7, "arousal": 0.75, "smile": 0.6, "energy": 0.85},
    "emotional": {"valence": 0.1, "arousal": 0.55, "smile": 0.2, "energy": 0.5},
    "confused": {"valence": -0.1, "arousal": 0.45, "smile": 0.1, "energy": 0.4},
    "shocked": {"valence": -0.3, "arousal": 0.9, "smile": 0.0, "energy": 0.85},
    "crying": {"valence": -0.85, "arousal": 0.7, "smile": 0.0, "energy": 0.55},
    "laughing": {"valence": 0.9, "arousal": 0.85, "smile": 0.95, "energy": 0.9},
    "smiling": {"valence": 0.7, "arousal": 0.4, "smile": 0.7, "energy": 0.5},
    "thinking": {"valence": 0.05, "arousal": 0.35, "smile": 0.1, "energy": 0.35},
    "proud": {"valence": 0.75, "arousal": 0.55, "smile": 0.65, "energy": 0.65},
    "nervous": {"valence": -0.35, "arousal": 0.7, "smile": 0.15, "energy": 0.6},
    "surprised": {"valence": 0.2, "arousal": 0.85, "smile": 0.3, "energy": 0.8},
}

_CUSTOM_EMOTIONS: dict[str, dict[str, Any]] = {}

_EXPRESSION_LIBRARY: dict[str, dict[str, Any]] = {
    "soft_smile": {"region": "mouth", "intensity": 0.4},
    "wide_smile": {"region": "mouth", "intensity": 0.85},
    "frown": {"region": "brow_mouth", "intensity": 0.7},
    "raised_brows": {"region": "eyebrow", "intensity": 0.6},
    "narrowed_eyes": {"region": "eye", "intensity": 0.55},
    "tearful": {"region": "eye", "intensity": 0.8},
    "open_mouth": {"region": "mouth", "intensity": 0.7},
    "tight_lips": {"region": "mouth", "intensity": 0.5},
}

_PERFORMANCE_LIBRARY: dict[str, dict[str, Any]] = {
    "open_gesture": {"hands": "open_palm", "energy": 0.5},
    "clenched_fist": {"hands": "fist", "energy": 0.8},
    "crossed_arms": {"hands": "folded", "energy": 0.4},
    "shrug": {"shoulders": "up", "energy": 0.45},
    "lean_forward": {"torso": "forward", "energy": 0.55},
    "withdraw": {"torso": "back", "energy": 0.35},
    "bounce_step": {"gait": "light", "energy": 0.7},
    "heavy_step": {"gait": "heavy", "energy": 0.6},
}


def register_emotion(emotion_id: str, spec: dict[str, Any]) -> None:
    key = (emotion_id or "").strip().lower().replace(" ", "_").replace("-", "_")
    if not key:
        raise ValueError("emotion_id is required")
    _CUSTOM_EMOTIONS[key] = {
        "valence": float(spec.get("valence") or 0.0),
        "arousal": float(spec.get("arousal") or 0.5),
        "smile": float(spec.get("smile") or 0.2),
        "energy": float(spec.get("energy") or 0.5),
        "custom": True,
    }


def resolve_emotion(emotion: str | None) -> str:
    key = (emotion or "calm").strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "joy": "happy",
        "sorrow": "sad",
        "mad": "angry",
        "scared": "fear",
        "tense": "suspense",
        "motivate": "motivational",
        "cry": "crying",
        "laugh": "laughing",
        "smile": "smiling",
        "think": "thinking",
        "shock": "shocked",
        "surprise": "surprised",
        "romance": "romantic",
    }
    key = aliases.get(key, key)
    catalog = {**_BUILTIN_EMOTIONS, **_CUSTOM_EMOTIONS}
    if key not in catalog:
        register_emotion(key, {"valence": 0.0, "arousal": 0.5, "smile": 0.2, "energy": 0.5})
    return key


def get_emotion_spec(emotion: str) -> dict[str, Any]:
    key = resolve_emotion(emotion)
    catalog = {**_BUILTIN_EMOTIONS, **_CUSTOM_EMOTIONS}
    return dict(catalog[key])


def list_emotion_library() -> dict[str, Any]:
    catalog = {**_BUILTIN_EMOTIONS, **_CUSTOM_EMOTIONS}
    return {
        "emotions": [{"emotion_id": k, **v} for k, v in sorted(catalog.items())],
        "expressions": [{"expression_id": k, **v} for k, v in _EXPRESSION_LIBRARY.items()],
        "performances": [
            {"performance_id": k, **v} for k, v in _PERFORMANCE_LIBRARY.items()
        ],
        "emotion_count": len(catalog),
        "expression_count": len(_EXPRESSION_LIBRARY),
        "performance_count": len(_PERFORMANCE_LIBRARY),
        "extensible": True,
    }


def get_expression_preset(expression_id: str) -> dict[str, Any] | None:
    return dict(_EXPRESSION_LIBRARY[expression_id]) if expression_id in _EXPRESSION_LIBRARY else None


def get_performance_preset(performance_id: str) -> dict[str, Any] | None:
    return (
        dict(_PERFORMANCE_LIBRARY[performance_id])
        if performance_id in _PERFORMANCE_LIBRARY
        else None
    )
