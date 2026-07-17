"""Shot / Lens / Preset libraries — extensible catalog."""

from __future__ import annotations

from typing import Any

from app.services.camera_intelligence.models import LensSelection

_BUILTIN_SHOTS: dict[str, dict[str, Any]] = {
    "extreme_wide_shot": {"category": "size", "default_duration": 4.0, "motion": "static", "focal_hint": 18},
    "wide_shot": {"category": "size", "default_duration": 3.5, "motion": "static", "focal_hint": 24},
    "full_shot": {"category": "size", "default_duration": 3.0, "motion": "static", "focal_hint": 35},
    "medium_shot": {"category": "size", "default_duration": 3.0, "motion": "static", "focal_hint": 50},
    "medium_close_up": {"category": "size", "default_duration": 2.5, "motion": "static", "focal_hint": 70},
    "close_up": {"category": "size", "default_duration": 2.5, "motion": "static", "focal_hint": 85},
    "extreme_close_up": {"category": "size", "default_duration": 2.0, "motion": "static", "focal_hint": 100},
    "over_the_shoulder": {"category": "relation", "default_duration": 3.0, "motion": "static", "focal_hint": 50},
    "pov": {"category": "relation", "default_duration": 2.5, "motion": "handheld", "focal_hint": 35},
    "drone_shot": {"category": "aerial", "default_duration": 5.0, "motion": "drone", "focal_hint": 24},
    "top_view": {"category": "angle", "default_duration": 3.0, "motion": "crane", "focal_hint": 28},
    "low_angle": {"category": "angle", "default_duration": 3.0, "motion": "static", "focal_hint": 35},
    "high_angle": {"category": "angle", "default_duration": 3.0, "motion": "static", "focal_hint": 35},
    "dutch_angle": {"category": "angle", "default_duration": 2.5, "motion": "static", "focal_hint": 35},
    "tracking_shot": {"category": "motion", "default_duration": 4.0, "motion": "tracking", "focal_hint": 35},
    "dolly_shot": {"category": "motion", "default_duration": 4.0, "motion": "dolly", "focal_hint": 40},
    "crane_shot": {"category": "motion", "default_duration": 5.0, "motion": "crane", "focal_hint": 28},
    "orbit_shot": {"category": "motion", "default_duration": 4.5, "motion": "orbit", "focal_hint": 35},
    "static_shot": {"category": "motion", "default_duration": 3.0, "motion": "static", "focal_hint": 50},
    "handheld": {"category": "motion", "default_duration": 3.0, "motion": "handheld", "focal_hint": 35},
    "cinematic_reveal": {"category": "style", "default_duration": 5.0, "motion": "dolly", "focal_hint": 28},
}

_CUSTOM_SHOTS: dict[str, dict[str, Any]] = {}

_LENSES: dict[str, LensSelection] = {
    "lens_18mm": LensSelection("lens_18mm", "Ultra Wide 18mm", 18.0, 2.8, "deep", "establishing"),
    "lens_24mm": LensSelection("lens_24mm", "Wide 24mm", 24.0, 2.8, "deep", "environment"),
    "lens_35mm": LensSelection("lens_35mm", "Standard Wide 35mm", 35.0, 2.0, "medium", "dialogue"),
    "lens_50mm": LensSelection("lens_50mm", "Normal 50mm", 50.0, 1.8, "medium", "portrait"),
    "lens_70mm": LensSelection("lens_70mm", "Short Tele 70mm", 70.0, 2.0, "shallow", "MCU"),
    "lens_85mm": LensSelection("lens_85mm", "Portrait 85mm", 85.0, 1.4, "shallow", "close_up"),
    "lens_100mm": LensSelection("lens_100mm", "Macro Tele 100mm", 100.0, 2.8, "very_shallow", "ECU"),
}

_PRESETS: dict[str, dict[str, Any]] = {
    "cinematic_drama": {"shots": ["wide_shot", "medium_shot", "close_up"], "grade": "teal_orange"},
    "action_coverage": {"shots": ["tracking_shot", "low_angle", "handheld"], "grade": "cool_steel"},
    "dialogue_coverage": {"shots": ["over_the_shoulder", "medium_close_up", "close_up"], "grade": "neutral"},
    "epic_establish": {"shots": ["extreme_wide_shot", "drone_shot", "cinematic_reveal"], "grade": "warm_gold"},
}


def register_shot(shot_id: str, spec: dict[str, Any]) -> None:
    key = (shot_id or "").strip().lower().replace(" ", "_").replace("-", "_")
    if not key:
        raise ValueError("shot_id is required")
    _CUSTOM_SHOTS[key] = {
        "category": spec.get("category") or "custom",
        "default_duration": float(spec.get("default_duration") or 3.0),
        "motion": spec.get("motion") or "static",
        "focal_hint": float(spec.get("focal_hint") or 50),
        "custom": True,
    }


def resolve_shot(shot: str | None) -> str:
    key = (shot or "medium_shot").strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "ews": "extreme_wide_shot",
        "ws": "wide_shot",
        "fs": "full_shot",
        "ms": "medium_shot",
        "mcu": "medium_close_up",
        "cu": "close_up",
        "ecu": "extreme_close_up",
        "ots": "over_the_shoulder",
        "reveal": "cinematic_reveal",
        "dolly": "dolly_shot",
        "crane": "crane_shot",
        "orbit": "orbit_shot",
        "track": "tracking_shot",
        "drone": "drone_shot",
    }
    key = aliases.get(key, key)
    catalog = {**_BUILTIN_SHOTS, **_CUSTOM_SHOTS}
    if key not in catalog:
        register_shot(key, {"category": "custom", "default_duration": 3.0})
    return key


def get_shot_spec(shot: str) -> dict[str, Any]:
    key = resolve_shot(shot)
    return dict({**_BUILTIN_SHOTS, **_CUSTOM_SHOTS}[key])


def select_lens_for_shot(shot_type: str) -> LensSelection:
    spec = get_shot_spec(shot_type)
    hint = float(spec.get("focal_hint") or 50)
    best = min(_LENSES.values(), key=lambda L: abs(L.focal_length_mm - hint))
    return best


def list_camera_library() -> dict[str, Any]:
    catalog = {**_BUILTIN_SHOTS, **_CUSTOM_SHOTS}
    return {
        "shots": [{"shot_id": k, **v} for k, v in sorted(catalog.items())],
        "lenses": [L.to_dict() for L in _LENSES.values()],
        "presets": [{"preset_id": k, **v} for k, v in _PRESETS.items()],
        "shot_count": len(catalog),
        "lens_count": len(_LENSES),
        "preset_count": len(_PRESETS),
        "extensible": True,
    }


def get_preset(preset_id: str | None) -> dict[str, Any] | None:
    if not preset_id:
        return None
    key = preset_id.strip().lower().replace("-", "_")
    return dict(_PRESETS[key]) if key in _PRESETS else None
