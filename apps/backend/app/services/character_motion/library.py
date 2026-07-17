"""Motion / Pose / Gesture libraries — extensible action catalog."""

from __future__ import annotations

from typing import Any

# Architecture supports unlimited future actions via register_action().
_BUILTIN_ACTIONS: dict[str, dict[str, Any]] = {
    "walking": {"category": "locomotion", "default_duration": 3.0, "engines": ["walking", "pose", "head", "eye"]},
    "running": {"category": "locomotion", "default_duration": 2.5, "engines": ["running", "pose", "head", "eye"]},
    "sitting": {"category": "posture", "default_duration": 2.0, "engines": ["sitting", "pose", "hand"]},
    "standing": {"category": "posture", "default_duration": 1.5, "engines": ["standing", "pose"]},
    "talking": {"category": "communication", "default_duration": 4.0, "engines": ["standing", "hand", "head", "facial", "eye"]},
    "listening": {"category": "communication", "default_duration": 3.0, "engines": ["standing", "head", "eye"]},
    "pointing": {"category": "gesture", "default_duration": 1.5, "engines": ["hand", "pose", "eye"]},
    "handshake": {"category": "gesture", "default_duration": 2.0, "engines": ["hand", "standing", "eye"]},
    "dancing": {"category": "performance", "default_duration": 5.0, "engines": ["walking", "hand", "head", "facial"]},
    "waving": {"category": "gesture", "default_duration": 1.5, "engines": ["hand", "standing", "facial"]},
    "looking_around": {"category": "attention", "default_duration": 2.5, "engines": ["head", "eye", "standing"]},
    "smiling": {"category": "expression", "default_duration": 1.2, "engines": ["facial", "eye", "head"]},
    "laughing": {"category": "expression", "default_duration": 2.0, "engines": ["facial", "head", "standing"]},
    "crying": {"category": "expression", "default_duration": 3.0, "engines": ["facial", "head", "eye"]},
    "thinking": {"category": "cognition", "default_duration": 2.5, "engines": ["head", "hand", "eye", "facial"]},
    "fighting": {"category": "action", "default_duration": 4.0, "engines": ["pose", "hand", "running", "head"]},
    "driving": {"category": "activity", "default_duration": 4.0, "engines": ["sitting", "hand", "eye", "head"]},
    "typing": {"category": "activity", "default_duration": 3.0, "engines": ["sitting", "hand", "eye"]},
    "reading": {"category": "activity", "default_duration": 3.5, "engines": ["sitting", "eye", "head", "hand"]},
    "writing": {"category": "activity", "default_duration": 3.0, "engines": ["sitting", "hand", "eye", "head"]},
    "custom": {"category": "custom", "default_duration": 2.0, "engines": ["pose", "standing"]},
}

_CUSTOM_ACTIONS: dict[str, dict[str, Any]] = {}

_POSE_LIBRARY: dict[str, dict[str, Any]] = {
    "idle_stand": {"spine": "upright", "hips": "neutral", "knees": "locked_soft"},
    "walk_left": {"spine": "upright", "hips": "swing_left", "knees": "flex"},
    "walk_right": {"spine": "upright", "hips": "swing_right", "knees": "flex"},
    "run_drive": {"spine": "forward_lean", "hips": "drive", "knees": "deep_flex"},
    "sit_neutral": {"spine": "upright", "hips": "seated", "knees": "bent_90"},
    "point_right": {"spine": "twist_right", "arm_r": "extended", "hand_r": "point"},
    "wave_right": {"spine": "upright", "arm_r": "raised", "hand_r": "wave"},
    "think_chin": {"spine": "slight_forward", "arm_r": "raised", "hand_r": "chin"},
}

_GESTURE_LIBRARY: dict[str, dict[str, Any]] = {
    "open_palm": {"hand": "open", "intensity": 0.5},
    "point_index": {"hand": "point", "intensity": 0.7},
    "wave": {"hand": "wave", "intensity": 0.6},
    "fist": {"hand": "fist", "intensity": 0.8},
    "handshake_reach": {"hand": "reach", "intensity": 0.65},
    "type_keys": {"hand": "typing", "intensity": 0.4},
    "write_pen": {"hand": "pen_grip", "intensity": 0.45},
}


def register_action(action_id: str, spec: dict[str, Any]) -> None:
    """Extend catalog with unlimited future actions."""
    key = (action_id or "").strip().lower().replace(" ", "_").replace("-", "_")
    if not key:
        raise ValueError("action_id is required")
    _CUSTOM_ACTIONS[key] = {
        "category": spec.get("category") or "custom",
        "default_duration": float(spec.get("default_duration") or 2.0),
        "engines": list(spec.get("engines") or ["pose", "standing"]),
        "custom": True,
    }


def resolve_action(action: str | None) -> str:
    key = (action or "standing").strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "walk": "walking",
        "run": "running",
        "sit": "sitting",
        "stand": "standing",
        "talk": "talking",
        "listen": "listening",
        "point": "pointing",
        "dance": "dancing",
        "wave": "waving",
        "look_around": "looking_around",
        "smile": "smiling",
        "laugh": "laughing",
        "cry": "crying",
        "think": "thinking",
        "fight": "fighting",
        "drive": "driving",
        "type": "typing",
        "read": "reading",
        "write": "writing",
    }
    key = aliases.get(key, key)
    catalog = {**_BUILTIN_ACTIONS, **_CUSTOM_ACTIONS}
    if key not in catalog:
        # Unknown → custom action slot (unlimited architecture)
        register_action(key, {"category": "custom", "default_duration": 2.0})
    return key


def get_action_spec(action: str) -> dict[str, Any]:
    key = resolve_action(action)
    catalog = {**_BUILTIN_ACTIONS, **_CUSTOM_ACTIONS}
    return dict(catalog[key])


def list_motion_library() -> dict[str, Any]:
    catalog = {**_BUILTIN_ACTIONS, **_CUSTOM_ACTIONS}
    return {
        "actions": [
            {"action_id": k, **v} for k, v in sorted(catalog.items())
        ],
        "poses": [{"pose_id": k, **v} for k, v in _POSE_LIBRARY.items()],
        "gestures": [{"gesture_id": k, **v} for k, v in _GESTURE_LIBRARY.items()],
        "action_count": len(catalog),
        "pose_count": len(_POSE_LIBRARY),
        "gesture_count": len(_GESTURE_LIBRARY),
        "extensible": True,
    }


def get_pose(pose_id: str) -> dict[str, Any] | None:
    return dict(_POSE_LIBRARY[pose_id]) if pose_id in _POSE_LIBRARY else None


def get_gesture(gesture_id: str) -> dict[str, Any] | None:
    return dict(_GESTURE_LIBRARY[gesture_id]) if gesture_id in _GESTURE_LIBRARY else None
