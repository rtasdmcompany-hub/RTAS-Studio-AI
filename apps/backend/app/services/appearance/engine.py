"""Character Style & Appearance Engine — public operations."""

from __future__ import annotations

from typing import Any

from app.services.appearance import store
from app.services.appearance.appearance_manager import set_outfit, set_style
from app.services.appearance.consistency import (
    validate_appearance,
    validate_outfit_preserves_identity,
)
from app.services.appearance.models import AppearanceProfile
from app.services.appearance.presets import get_preset, list_presets, preset_payload
from app.services.appearance.version import ENGINE_LABEL, ENGINE_NAME, ENGINE_VERSION


def apply_style(
    character_id: str,
    **kwargs: Any,
) -> dict[str, Any]:
    record = set_style(character_id, **kwargs)
    preset = get_preset(record.style_preset_id)
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
        **record.to_dict(),
        "style_preset": preset.to_dict() if preset else None,
        "presets_available": [p.preset_id for p in list_presets()],
    }


def apply_outfit(
    character_id: str,
    **kwargs: Any,
) -> dict[str, Any]:
    before = store.get_by_character(character_id)
    before_profile = before.profile if before else None
    record = set_outfit(character_id, **kwargs)
    identity_check = None
    if before_profile:
        identity_check = validate_outfit_preserves_identity(before_profile, record.profile)
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
        **record.to_dict(),
        "identity_preserved": True if identity_check is None else identity_check["ok"],
        "identity_check": identity_check,
        "active_outfit": next(
            (o.to_dict() for o in record.outfits if o.outfit_id == record.active_outfit_id),
            None,
        ),
    }


def get_style(character_id: str) -> dict[str, Any] | None:
    record = store.get_by_character(character_id)
    if not record:
        # Lazy-create baseline appearance from character DNA when available
        try:
            record = set_style(character_id)
        except ValueError:
            return None
    preset = get_preset(record.style_preset_id)
    consistency = validate_appearance(record)
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
        **record.to_dict(),
        "style_preset": preset.to_dict() if preset else None,
        "consistency": consistency.to_dict(),
        "presets": preset_payload()["presets"],
    }


def get_outfits(character_id: str) -> dict[str, Any] | None:
    record = store.get_by_character(character_id)
    if not record:
        try:
            record = set_style(character_id)
        except ValueError:
            return None
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "character_id": character_id,
        "active_outfit_id": record.active_outfit_id,
        "outfits": [o.to_dict() for o in record.outfits],
        "count": len(record.outfits),
        "facial_fingerprint": record.profile.facial_fingerprint(),
        "profile_snapshot": {
            "clothing_style": record.profile.clothing_style,
            "shoes": record.profile.shoes,
            "accessories": list(record.profile.accessories),
            # Identity fields included to prove outfit APIs don't hide them
            "hairstyle": record.profile.hairstyle,
            "eye_color": record.profile.eye_color,
            "skin_tone": record.profile.skin_tone,
        },
    }


def detect_drift(
    character_id: str,
    *,
    candidate_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    record = store.get_by_character(character_id)
    if not record:
        record = set_style(character_id)
    candidate = None
    if candidate_overrides:
        data = record.profile.to_dict()
        data.update({k: v for k, v in candidate_overrides.items() if v is not None})
        if "accessories" in candidate_overrides and candidate_overrides["accessories"] is not None:
            data["accessories"] = list(candidate_overrides["accessories"])
        candidate = AppearanceProfile(**data)
    report = validate_appearance(record, candidate=candidate)
    record.last_consistency = report
    store.save(record)
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        **report.to_dict(),
    }


def style_dict(**kwargs: Any) -> dict[str, Any]:
    return apply_style(**kwargs)


def outfit_dict(**kwargs: Any) -> dict[str, Any]:
    return apply_outfit(**kwargs)
