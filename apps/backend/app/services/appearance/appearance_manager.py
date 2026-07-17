"""Appearance Manager — build and update permanent appearance profiles."""

from __future__ import annotations

import hashlib
import time
from typing import Any

from app.services.appearance import store
from app.services.appearance.accessories import apply_accessories, normalize_accessories
from app.services.appearance.consistency import validate_appearance
from app.services.appearance.hairstyle import (
    apply_hairstyle,
    normalize_beard,
    normalize_hair_color,
    normalize_hairstyle,
)
from app.services.appearance.models import AppearanceProfile, AppearanceRecord
from app.services.appearance.outfits import (
    apply_outfit_to_profile,
    build_default_outfits,
    create_custom_outfit,
    find_outfit,
    resolve_category,
)
from app.services.appearance.presets import get_preset, resolve_preset_id
from app.services.appearance.version import ENGINE_VERSION


def _profile_id(character_id: str) -> str:
    digest = hashlib.sha1(f"appear|{character_id}|{ENGINE_VERSION}".encode()).hexdigest()
    return f"apar_{digest[:12]}"


def _load_character_dict(character_id: str) -> dict[str, Any] | None:
    try:
        from app.services.character_generation.engine import get_character

        record = get_character(character_id)
        if record:
            return record.to_dict()
    except Exception:
        pass
    try:
        from app.services.character_generation import get_character as get_char_pkg

        record = get_char_pkg(character_id)
        if record:
            return record.to_dict()
    except Exception:
        pass
    return None


def profile_from_character(character: dict[str, Any] | None = None) -> AppearanceProfile:
    c = character or {}
    identity = c.get("identity") if isinstance(c.get("identity"), dict) else c
    hairstyle = normalize_hairstyle(
        identity.get("hairstyle") or c.get("hairstyle"), "short"
    )
    beard = normalize_beard(identity.get("beard") or c.get("beard"), "none")
    skin = str(identity.get("skin") or identity.get("skin_tone") or c.get("skin") or "medium")
    body = str(identity.get("body_type") or c.get("body_type") or "average")
    eye = str(identity.get("eye_color") or c.get("eye_color") or "brown")
    clothing = str(
        identity.get("clothing")
        or c.get("clothing")
        or c.get("clothing_style")
        or "casual_everyday"
    )
    accessories = normalize_accessories(
        identity.get("accessories") if isinstance(identity.get("accessories"), list) else c.get("accessories")
    )
    hair_color = normalize_hair_color(
        c.get("hair_color") or identity.get("hair_color"), "brown"
    )
    height = str(c.get("height") or identity.get("height") or "average")
    shoes = str(c.get("shoes") or identity.get("shoes") or "sneakers")
    return AppearanceProfile(
        hairstyle=hairstyle,
        hair_color=hair_color,
        beard_style=beard,
        eye_color=eye,
        skin_tone=skin,
        body_type=body,
        height=height,
        clothing_style=clothing,
        shoes=shoes,
        accessories=accessories or ["watch"],
    )


def profile_from_overrides(
    base: AppearanceProfile,
    overrides: dict[str, Any] | None,
) -> AppearanceProfile:
    if not overrides:
        return base
    data = base.to_dict()
    for key in list(data.keys()):
        if key == "accessories":
            continue
        if key in overrides and overrides[key] is not None:
            data[key] = overrides[key]
    if "hairstyle" in overrides and overrides["hairstyle"] is not None:
        data["hairstyle"] = normalize_hairstyle(str(overrides["hairstyle"]))
    if "hair_color" in overrides and overrides["hair_color"] is not None:
        data["hair_color"] = normalize_hair_color(str(overrides["hair_color"]))
    if "beard_style" in overrides and overrides["beard_style"] is not None:
        data["beard_style"] = normalize_beard(str(overrides["beard_style"]))
    if "accessories" in overrides and overrides["accessories"] is not None:
        data["accessories"] = normalize_accessories(list(overrides["accessories"]))
    return AppearanceProfile(**data)


def ensure_appearance(
    character_id: str,
    *,
    style_preset: str | None = None,
    overrides: dict[str, Any] | None = None,
) -> AppearanceRecord:
    cid = (character_id or "").strip()
    if not cid:
        raise ValueError("character_id is required")

    existing = store.get_by_character(cid)
    char_dict = _load_character_dict(cid) or {"character_id": cid}
    base = profile_from_character(char_dict)
    if existing:
        base = existing.profile
    profile = profile_from_overrides(base, overrides)

    outfits = list(existing.outfits) if existing else build_default_outfits(cid)
    active = existing.active_outfit_id if existing else (outfits[0].outfit_id if outfits else None)
    preset_id = resolve_preset_id(style_preset) or (
        existing.style_preset_id if existing else "realistic"
    )
    if style_preset and not get_preset(style_preset):
        raise ValueError(f"Unknown style preset: {style_preset}")

    record = AppearanceRecord(
        profile_id=existing.profile_id if existing else _profile_id(cid),
        character_id=cid,
        profile=profile,
        active_outfit_id=active,
        outfits=outfits,
        style_preset_id=preset_id,
        version=(existing.version + 1) if existing and overrides else (existing.version if existing else 1),
        production_ready=True,
        metadata={
            "engine_version": ENGINE_VERSION,
            "updated_at": time.time(),
            "source_character": bool(char_dict.get("identity") or char_dict.get("character_id")),
        },
    )
    record.last_consistency = validate_appearance(record)
    store.save(record)
    return record


def set_style(
    character_id: str,
    *,
    style_preset: str | None = None,
    overrides: dict[str, Any] | None = None,
    hairstyle: str | None = None,
    hair_color: str | None = None,
    beard_style: str | None = None,
    eye_color: str | None = None,
    skin_tone: str | None = None,
    body_type: str | None = None,
    height: str | None = None,
    clothing_style: str | None = None,
    shoes: str | None = None,
    accessories: list[str] | None = None,
) -> AppearanceRecord:
    merged = dict(overrides or {})
    for key, value in (
        ("hairstyle", hairstyle),
        ("hair_color", hair_color),
        ("beard_style", beard_style),
        ("eye_color", eye_color),
        ("skin_tone", skin_tone),
        ("body_type", body_type),
        ("height", height),
        ("clothing_style", clothing_style),
        ("shoes", shoes),
        ("accessories", accessories),
    ):
        if value is not None:
            merged[key] = value
    record = ensure_appearance(
        character_id, style_preset=style_preset, overrides=merged or None
    )
    if hairstyle or hair_color or beard_style:
        record.profile = apply_hairstyle(
            record.profile,
            hairstyle=hairstyle,
            hair_color=hair_color,
            beard_style=beard_style,
        )
    if accessories is not None:
        record.profile = apply_accessories(record.profile, accessories, replace=True)
    record.last_consistency = validate_appearance(record)
    store.save(record)
    return record


def set_outfit(
    character_id: str,
    *,
    outfit_id: str | None = None,
    category: str | None = None,
    custom_name: str | None = None,
    clothing_style: str | None = None,
    shoes: str | None = None,
    accessories: list[str] | None = None,
) -> AppearanceRecord:
    record = ensure_appearance(character_id)
    facial_before = record.profile.facial_fingerprint()

    outfit = find_outfit(record.outfits, outfit_id=outfit_id, category=category)
    if not outfit and custom_name:
        outfit = create_custom_outfit(
            character_id,
            name=custom_name,
            clothing_style=clothing_style or "custom_look",
            shoes=shoes or "custom_shoes",
            accessories=accessories,
        )
        record.outfits.append(outfit)
    if not outfit and category:
        # create from category defaults if somehow missing
        resolve_category(category)
        defaults = build_default_outfits(character_id)
        outfit = find_outfit(defaults, category=category)
        if outfit and outfit.outfit_id not in {o.outfit_id for o in record.outfits}:
            record.outfits.append(outfit)
    if not outfit:
        raise ValueError("outfit_id or category (or custom outfit fields) required")

    # Optional field overrides for custom/category tweak — still outfit-only
    if clothing_style or shoes or accessories is not None:
        outfit = type(outfit)(
            outfit_id=outfit.outfit_id,
            category=outfit.category,
            name=outfit.name,
            clothing_style=clothing_style or outfit.clothing_style,
            shoes=shoes or outfit.shoes,
            accessories=(
                normalize_accessories(accessories)
                if accessories is not None
                else list(outfit.accessories)
            ),
            description=outfit.description,
            custom=outfit.custom,
        )
        # replace in list
        record.outfits = [
            outfit if o.outfit_id == outfit.outfit_id else o for o in record.outfits
        ]

    record.profile = apply_outfit_to_profile(record.profile, outfit)
    record.active_outfit_id = outfit.outfit_id
    record.version += 1

    if record.profile.facial_fingerprint() != facial_before:
        raise ValueError("Outfit change must never alter facial identity")

    record.last_consistency = validate_appearance(record)
    record.metadata["last_outfit_switch"] = {
        "outfit_id": outfit.outfit_id,
        "category": outfit.category,
        "facial_fingerprint": facial_before,
        "identity_preserved": True,
    }
    store.save(record)
    return record
