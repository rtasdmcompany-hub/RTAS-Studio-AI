"""Professional camera motion catalog — specs, lenses, display names."""

from __future__ import annotations

from typing import Any

from app.services.camera_motion.models import CameraMotionKind

MOTION_KINDS: tuple[CameraMotionKind, ...] = (
    "dolly",
    "crane",
    "drone",
    "orbit",
    "slider",
    "tracking",
    "push_in",
    "pull_out",
    "pov",
    "steadicam",
    "handheld",
    "static",
)

DISPLAY_NAME: dict[CameraMotionKind, str] = {
    "dolly": "Dolly",
    "crane": "Crane",
    "drone": "Drone",
    "orbit": "Orbit",
    "slider": "Slider",
    "tracking": "Tracking",
    "push_in": "Push In",
    "pull_out": "Pull Out",
    "pov": "POV",
    "steadicam": "Steadicam",
    "handheld": "Handheld",
    "static": "Static",
}

# Default professional parameters per motion kind
MOTION_SPECS: dict[CameraMotionKind, dict[str, Any]] = {
    "dolly": {
        "ease": "ease_in_out",
        "subject_lock": True,
        "shake": 0.0,
        "lens_hint": "35mm narrative",
        "axis": "z",
        "description": "Smooth wheeled move on track toward/away subject",
    },
    "crane": {
        "ease": "ease_in_out",
        "subject_lock": True,
        "shake": 0.0,
        "lens_hint": "24mm wide",
        "axis": "y",
        "description": "Vertical / arc boom reveal or descent",
    },
    "drone": {
        "ease": "ease_out",
        "subject_lock": False,
        "shake": 0.02,
        "lens_hint": "24mm wide",
        "axis": "xyz",
        "description": "Aerial establish / flyover with altitude authority",
    },
    "orbit": {
        "ease": "ease_in_out",
        "subject_lock": True,
        "shake": 0.0,
        "lens_hint": "50mm natural",
        "axis": "yaw",
        "description": "Circular move around subject keeping face readable",
    },
    "slider": {
        "ease": "linear",
        "subject_lock": True,
        "shake": 0.0,
        "lens_hint": "50mm natural",
        "axis": "x",
        "description": "Short lateral precision slide with parallax",
    },
    "tracking": {
        "ease": "ease_in_out",
        "subject_lock": True,
        "shake": 0.05,
        "lens_hint": "35mm narrative",
        "axis": "follow",
        "description": "Follow subject locomotion with matched tempo",
    },
    "push_in": {
        "ease": "ease_in_out",
        "subject_lock": True,
        "shake": 0.0,
        "lens_hint": "85mm portrait",
        "axis": "z",
        "description": "Motivational push into emotional / detail beat",
    },
    "pull_out": {
        "ease": "ease_out",
        "subject_lock": False,
        "shake": 0.0,
        "lens_hint": "35mm narrative",
        "axis": "z",
        "description": "Reveal context / exit emotional intensity",
    },
    "pov": {
        "ease": "ease_in_out",
        "subject_lock": False,
        "shake": 0.12,
        "lens_hint": "35mm narrative",
        "axis": "head",
        "description": "Subject eye-line / embodied viewpoint",
    },
    "steadicam": {
        "ease": "ease_in_out",
        "subject_lock": True,
        "shake": 0.03,
        "lens_hint": "35mm narrative",
        "axis": "follow",
        "description": "Floating stabilized walk-and-talk / follow",
    },
    "handheld": {
        "ease": "linear",
        "subject_lock": True,
        "shake": 0.35,
        "lens_hint": "35mm narrative",
        "axis": "organic",
        "description": "Documentary / tension organic micro-jitter",
    },
    "static": {
        "ease": "linear",
        "subject_lock": True,
        "shake": 0.0,
        "lens_hint": "50mm natural",
        "axis": "none",
        "description": "Locked-off tripod; performance carries the frame",
    },
}

# Map free-text / scene-breakdown labels → canonical kinds
_ALIASES: dict[str, CameraMotionKind] = {
    "dolly": "dolly",
    "slow dolly": "dolly",
    "dolly in": "push_in",
    "dolly out": "pull_out",
    "crane": "crane",
    "jib": "crane",
    "boom": "crane",
    "drone": "drone",
    "aerial": "drone",
    "flyover": "drone",
    "orbit": "orbit",
    "arc": "orbit",
    "360": "orbit",
    "slider": "slider",
    "slide": "slider",
    "lateral": "slider",
    "tracking": "tracking",
    "track": "tracking",
    "follow": "tracking",
    "push in": "push_in",
    "push-in": "push_in",
    "pushin": "push_in",
    "push": "push_in",
    "pull out": "pull_out",
    "pull-out": "pull_out",
    "pullout": "pull_out",
    "pull back": "pull_out",
    "reveal": "pull_out",
    "pov": "pov",
    "point of view": "pov",
    "first person": "pov",
    "steadicam": "steadicam",
    "steadi": "steadicam",
    "gimbal": "steadicam",
    "handheld": "handheld",
    "hand held": "handheld",
    "hand-held": "handheld",
    "static": "static",
    "static hold": "static",
    "locked": "static",
    "tripod": "static",
}


def normalize_motion(value: str | None) -> CameraMotionKind | None:
    if not value:
        return None
    key = value.strip().lower().replace("_", " ")
    if key in _ALIASES:
        return _ALIASES[key]
    # Fuzzy contains
    for alias, kind in _ALIASES.items():
        if alias in key or key in alias:
            return kind
    for kind in MOTION_KINDS:
        if kind.replace("_", " ") in key or DISPLAY_NAME[kind].lower() in key:
            return kind
    return None


def display(kind: CameraMotionKind) -> str:
    return DISPLAY_NAME.get(kind, kind)


def spec(kind: CameraMotionKind) -> dict[str, Any]:
    return dict(MOTION_SPECS.get(kind, MOTION_SPECS["static"]))
