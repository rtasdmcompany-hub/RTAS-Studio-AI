"""Sub-engines: pose, walk/run/sit/stand, hands, head, eyes, facial."""

from __future__ import annotations

import hashlib
from typing import Any

from app.services.character_motion.library import get_gesture, get_pose
from app.services.character_motion.models import PoseKeyframe


def _pose_id(name: str, t: float) -> str:
    digest = hashlib.sha1(f"{name}|{t}".encode()).hexdigest()
    return f"pose_{digest[:10]}"


def build_pose_sequence(action: str, duration: float, emotion_bias: dict[str, float]) -> list[PoseKeyframe]:
    pose_map = {
        "walking": ["idle_stand", "walk_left", "walk_right", "idle_stand"],
        "running": ["idle_stand", "run_drive", "run_drive", "idle_stand"],
        "sitting": ["idle_stand", "sit_neutral"],
        "standing": ["idle_stand"],
        "pointing": ["idle_stand", "point_right"],
        "waving": ["idle_stand", "wave_right"],
        "thinking": ["idle_stand", "think_chin"],
        "handshake": ["idle_stand", "point_right", "idle_stand"],
    }
    names = pose_map.get(action, ["idle_stand", "idle_stand"])
    lean = float(emotion_bias.get("spine_lean", 0.0))
    poses: list[PoseKeyframe] = []
    step = duration / max(1, len(names) - 1) if len(names) > 1 else duration
    for i, name in enumerate(names):
        base = get_pose(name) or {"spine": "upright"}
        joints = dict(base)
        if lean:
            joints["emotion_lean"] = lean
        poses.append(
            PoseKeyframe(
                pose_id=_pose_id(name, i * step),
                name=name,
                joints=joints,
                timestamp_sec=round(i * step, 3),
            )
        )
    return poses


def walking_engine(style: str, emotion_bias: dict[str, float]) -> dict[str, Any]:
    return {
        "engine": "walking",
        "gait": style or "natural",
        "stride_scale": round(1.0 + float(emotion_bias.get("stride", 0.0)), 3),
        "cadence": round(1.0 + float(emotion_bias.get("cadence", 0.0)), 3),
        "arm_swing": round(0.5 + float(emotion_bias.get("arm_swing", 0.0)), 3),
        "preserve_body": True,
    }


def running_engine(style: str, emotion_bias: dict[str, float]) -> dict[str, Any]:
    return {
        "engine": "running",
        "gait": style or "athletic",
        "stride_scale": round(1.2 + float(emotion_bias.get("stride", 0.0)), 3),
        "cadence": round(1.35 + float(emotion_bias.get("cadence", 0.0)), 3),
        "forward_lean": round(0.2 + float(emotion_bias.get("spine_lean", 0.0)), 3),
        "preserve_body": True,
    }


def sitting_engine(emotion_bias: dict[str, float]) -> dict[str, Any]:
    return {
        "engine": "sitting",
        "posture": "seated_neutral",
        "spine_curve": round(0.1 + abs(float(emotion_bias.get("spine_lean", 0.0))), 3),
        "preserve_body": True,
    }


def standing_engine(emotion_bias: dict[str, float]) -> dict[str, Any]:
    return {
        "engine": "standing",
        "posture": "standing_neutral",
        "weight_shift": round(0.05 + abs(float(emotion_bias.get("weight_shift", 0.0))), 3),
        "preserve_body": True,
    }


def hand_gesture_engine(action: str, gesture_style: str, emotion_bias: dict[str, float]) -> list[dict[str, Any]]:
    mapping = {
        "pointing": "point_index",
        "waving": "wave",
        "handshake": "handshake_reach",
        "typing": "type_keys",
        "writing": "write_pen",
        "talking": "open_palm",
        "thinking": "open_palm",
        "fighting": "fist",
    }
    gid = mapping.get(action, "open_palm")
    base = get_gesture(gid) or {"hand": "open", "intensity": 0.5}
    intensity = min(1.0, float(base.get("intensity", 0.5)) + float(emotion_bias.get("gesture_amp", 0.0)))
    return [
        {
            "gesture_id": gid,
            "style": gesture_style or "natural",
            "hand": base.get("hand"),
            "intensity": round(intensity, 3),
            "preserve_proportions": True,
        }
    ]


def head_movement_engine(style: str, action: str, emotion_bias: dict[str, float]) -> dict[str, Any]:
    yaw = 0.15 if action in ("looking_around", "listening") else 0.05
    pitch = 0.08 if action in ("thinking", "reading") else 0.03
    return {
        "engine": "head",
        "style": style or "subtle",
        "yaw_amp": round(yaw + float(emotion_bias.get("head_yaw", 0.0)), 3),
        "pitch_amp": round(pitch + float(emotion_bias.get("head_pitch", 0.0)), 3),
        "nod": action in ("listening", "talking"),
        "preserve_identity": True,
    }


def eye_movement_engine(eye_contact: str, action: str, emotion_bias: dict[str, float]) -> dict[str, Any]:
    saccade = 0.4 if action in ("looking_around", "reading") else 0.15
    return {
        "engine": "eye",
        "eye_contact": eye_contact or "natural",
        "saccade_rate": round(saccade + float(emotion_bias.get("saccade", 0.0)), 3),
        "blink_rate": round(0.2 + float(emotion_bias.get("blink", 0.0)), 3),
        "gaze_target": "camera" if action in ("talking", "smiling") else "environment",
        "preserve_identity": True,
    }


def facial_expression_engine(emotion: str, action: str) -> dict[str, Any]:
    expression_map = {
        "smiling": "smile",
        "laughing": "laugh",
        "crying": "cry",
        "thinking": "thoughtful",
        "talking": "speaking",
        "angry": "frown",
    }
    expr = expression_map.get(action) or emotion
    return {
        "engine": "facial",
        "expression": expr,
        "emotion": emotion,
        "intensity": 0.7 if action in ("laughing", "crying", "angry") else 0.45,
        "face_lock_respected": True,
        "no_identity_drift": True,
    }
