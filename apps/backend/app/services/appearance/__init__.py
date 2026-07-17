"""RTAS Studio AI — AI Character Style & Appearance Engine (Phase 5 Sprint 3)."""

from app.services.appearance.engine import (
    apply_outfit,
    apply_style,
    detect_drift,
    get_outfits,
    get_style,
    outfit_dict,
    style_dict,
)
from app.services.appearance import store
from app.services.appearance.models import APPEARANCE_PROFILE_FIELDS, FACIAL_IDENTITY_FIELDS
from app.services.appearance.presets import list_presets, preset_payload
from app.services.appearance.version import (
    APPEARANCE_DRIFT_THRESHOLD,
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
)

__all__ = [
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "ENGINE_LABEL",
    "APPEARANCE_DRIFT_THRESHOLD",
    "APPEARANCE_PROFILE_FIELDS",
    "FACIAL_IDENTITY_FIELDS",
    "apply_style",
    "apply_outfit",
    "style_dict",
    "outfit_dict",
    "get_style",
    "get_outfits",
    "detect_drift",
    "list_presets",
    "preset_payload",
    "store",
]
