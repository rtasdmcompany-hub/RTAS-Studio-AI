"""Professional shot type catalog and cinematic defaults."""

from __future__ import annotations

SHOT_TYPES: tuple[str, ...] = (
    "Wide Shot",
    "Extreme Wide",
    "Medium Shot",
    "Close Up",
    "Extreme Close Up",
    "Over Shoulder",
    "POV",
    "Drone",
    "Tracking",
    "Crane",
    "Dutch Angle",
    "Top View",
    "Low Angle",
    "High Angle",
    "Handheld",
    "Steadicam",
    "Reveal",
    "Push In",
    "Pull Out",
    "Orbit",
    "Slider",
)

_LENS_FOR_SHOT: dict[str, str] = {
    "Extreme Wide": "24mm wide",
    "Wide Shot": "24mm wide",
    "Drone": "24mm wide",
    "Medium Shot": "35mm narrative",
    "Tracking": "35mm narrative",
    "Steadicam": "35mm narrative",
    "Over Shoulder": "50mm natural",
    "POV": "35mm narrative",
    "Close Up": "85mm portrait",
    "Extreme Close Up": "Macro lens",
    "Orbit": "50mm natural",
    "Reveal": "24mm wide",
    "Push In": "85mm portrait",
    "Pull Out": "35mm narrative",
    "Slider": "50mm natural",
    "Crane": "24mm wide",
    "Dutch Angle": "35mm narrative",
    "Top View": "24mm wide",
    "Low Angle": "35mm narrative",
    "High Angle": "35mm narrative",
    "Handheld": "35mm narrative",
}

_ANGLE_DEFAULTS: dict[str, str] = {
    "Drone": "High Angle",
    "Top View": "Top View",
    "Low Angle": "Low Angle",
    "High Angle": "High Angle",
    "Dutch Angle": "Dutch Angle",
    "Close Up": "Eye Level",
    "Extreme Close Up": "Eye Level",
    "POV": "Eye Level",
}

_DOF_FOR_SHOT: dict[str, str] = {
    "Close Up": "shallow DOF — eyes sharp",
    "Extreme Close Up": "ultra-shallow DOF — texture sharp",
    "Extreme Wide": "deep focus — environment readable",
    "Wide Shot": "deep focus",
    "Drone": "deep focus",
    "Medium Shot": "moderate DOF",
}


def normalize_shot_type(value: str) -> str:
    lower = (value or "").strip().lower()
    for shot in SHOT_TYPES:
        if shot.lower() == lower:
            return shot
    aliases = {
        "wide": "Wide Shot",
        "ewide": "Extreme Wide",
        "extreme wide shot": "Extreme Wide",
        "cu": "Close Up",
        "ecu": "Extreme Close Up",
        "ots": "Over Shoulder",
        "over the shoulder": "Over Shoulder",
        "dolly": "Push In",
        "slow dolly": "Push In",
    }
    return aliases.get(lower, value if value else "Medium Shot")


def lens_for_shot(shot_type: str, fallback: str = "35mm narrative") -> str:
    return _LENS_FOR_SHOT.get(normalize_shot_type(shot_type), fallback)


def angle_for_shot(shot_type: str, preferred: str | None = None) -> str:
    if preferred:
        return preferred
    return _ANGLE_DEFAULTS.get(normalize_shot_type(shot_type), "Eye Level")


def dof_for_shot(shot_type: str) -> str:
    return _DOF_FOR_SHOT.get(normalize_shot_type(shot_type), "cinematic mid DOF")


def composition_for_shot(shot_type: str, *, flashback: bool = False) -> str:
    shot = normalize_shot_type(shot_type)
    if flashback:
        return "soft vignette, center-weighted memory frame"
    if shot in ("Close Up", "Extreme Close Up"):
        return "rule of thirds — eyes on upper third"
    if shot in ("Extreme Wide", "Wide Shot", "Drone"):
        return "leading lines into subject; negative space for loneliness"
    if shot == "Over Shoulder":
        return "over-shoulder depth stack; subject framed in look-space"
    if shot == "Tracking":
        return "profile / three-quarter track with foreground parallax"
    return "balanced cinematic frame; clear subject hierarchy"
