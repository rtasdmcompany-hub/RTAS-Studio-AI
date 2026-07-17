"""Outfit Manager — multiple outfits; never mutates facial identity."""

from __future__ import annotations

import hashlib
from typing import Any

from app.services.appearance.models import (
    AppearanceProfile,
    OutfitCategory,
    OutfitDefinition,
)

_DEFAULT_OUTFITS: list[dict[str, Any]] = [
    {
        "category": "casual",
        "name": "Casual",
        "clothing_style": "casual_everyday",
        "shoes": "sneakers",
        "accessories": ["watch"],
        "description": "Relaxed everyday wear",
    },
    {
        "category": "formal",
        "name": "Formal",
        "clothing_style": "formal_evening",
        "shoes": "dress_shoes",
        "accessories": ["cufflinks"],
        "description": "Evening formal attire",
    },
    {
        "category": "business",
        "name": "Business",
        "clothing_style": "business_suit",
        "shoes": "oxfords",
        "accessories": ["briefcase_strap"],
        "description": "Professional business look",
    },
    {
        "category": "traditional",
        "name": "Traditional",
        "clothing_style": "traditional_cultural",
        "shoes": "traditional_footwear",
        "accessories": ["heritage_accessory"],
        "description": "Cultural / traditional dress",
    },
    {
        "category": "luxury",
        "name": "Luxury",
        "clothing_style": "luxury_designer",
        "shoes": "designer_loafers",
        "accessories": ["statement_jewelry"],
        "description": "High-end designer wardrobe",
    },
    {
        "category": "sports",
        "name": "Sports",
        "clothing_style": "athletic_wear",
        "shoes": "running_shoes",
        "accessories": ["fitness_band"],
        "description": "Athletic / sports kit",
    },
]


def _outfit_id(character_id: str, category: str, name: str) -> str:
    digest = hashlib.sha1(f"{character_id}|{category}|{name}".encode()).hexdigest()
    return f"outfit_{digest[:12]}"


def resolve_category(category: str | None) -> OutfitCategory:
    c = (category or "casual").strip().lower()
    valid = {
        "casual",
        "formal",
        "business",
        "traditional",
        "luxury",
        "sports",
        "custom",
    }
    if c not in valid:
        raise ValueError(f"Invalid outfit category: {category}")
    return c  # type: ignore[return-value]


def build_default_outfits(character_id: str) -> list[OutfitDefinition]:
    outfits: list[OutfitDefinition] = []
    for spec in _DEFAULT_OUTFITS:
        cat = resolve_category(str(spec["category"]))
        name = str(spec["name"])
        outfits.append(
            OutfitDefinition(
                outfit_id=_outfit_id(character_id, cat, name),
                category=cat,
                name=name,
                clothing_style=str(spec["clothing_style"]),
                shoes=str(spec["shoes"]),
                accessories=list(spec.get("accessories") or []),
                description=str(spec.get("description") or ""),
                custom=False,
            )
        )
    return outfits


def create_custom_outfit(
    character_id: str,
    *,
    name: str,
    clothing_style: str,
    shoes: str,
    accessories: list[str] | None = None,
    description: str = "",
) -> OutfitDefinition:
    cat: OutfitCategory = "custom"
    label = (name or "Custom").strip() or "Custom"
    return OutfitDefinition(
        outfit_id=_outfit_id(character_id, cat, label),
        category=cat,
        name=label,
        clothing_style=(clothing_style or "custom_look").strip(),
        shoes=(shoes or "custom_shoes").strip(),
        accessories=list(accessories or []),
        description=description or "Custom outfit",
        custom=True,
    )


def find_outfit(
    outfits: list[OutfitDefinition],
    *,
    outfit_id: str | None = None,
    category: str | None = None,
) -> OutfitDefinition | None:
    if outfit_id:
        for o in outfits:
            if o.outfit_id == outfit_id:
                return o
    if category:
        cat = resolve_category(category)
        for o in outfits:
            if o.category == cat:
                return o
    return None


def apply_outfit_to_profile(
    profile: AppearanceProfile,
    outfit: OutfitDefinition,
) -> AppearanceProfile:
    """Switch clothing/shoes/accessories only — facial identity fields unchanged."""
    return AppearanceProfile(
        hairstyle=profile.hairstyle,
        hair_color=profile.hair_color,
        beard_style=profile.beard_style,
        eye_color=profile.eye_color,
        skin_tone=profile.skin_tone,
        body_type=profile.body_type,
        height=profile.height,
        clothing_style=outfit.clothing_style,
        shoes=outfit.shoes,
        accessories=list(outfit.accessories),
    )
