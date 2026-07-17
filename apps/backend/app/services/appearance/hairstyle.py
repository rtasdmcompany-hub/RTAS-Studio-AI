"""Hairstyle Manager — locked hair appearance traits."""

from __future__ import annotations

from typing import Any

from app.services.appearance.models import AppearanceProfile

_HAIRSTYLE_CATALOG = (
    "short",
    "short_textured",
    "medium",
    "long",
    "long_wavy",
    "bob",
    "buzz_cut",
    "ponytail",
    "braids",
    "curly",
)

_HAIR_COLORS = (
    "black",
    "brown",
    "dark_brown",
    "blonde",
    "auburn",
    "red",
    "grey",
    "silver",
)

_BEARD_STYLES = (
    "none",
    "stubble",
    "short_beard",
    "full_beard",
    "goatee",
    "mustache",
)


def normalize_hairstyle(value: str | None, default: str = "short") -> str:
    v = (value or default).strip().lower().replace(" ", "_")
    return v or default


def normalize_hair_color(value: str | None, default: str = "brown") -> str:
    v = (value or default).strip().lower().replace(" ", "_")
    return v or default


def normalize_beard(value: str | None, default: str = "none") -> str:
    v = (value or default).strip().lower().replace(" ", "_")
    return v or default


def apply_hairstyle(
    profile: AppearanceProfile,
    *,
    hairstyle: str | None = None,
    hair_color: str | None = None,
    beard_style: str | None = None,
) -> AppearanceProfile:
    data = profile.to_dict()
    if hairstyle is not None:
        data["hairstyle"] = normalize_hairstyle(hairstyle, profile.hairstyle)
    if hair_color is not None:
        data["hair_color"] = normalize_hair_color(hair_color, profile.hair_color)
    if beard_style is not None:
        data["beard_style"] = normalize_beard(beard_style, profile.beard_style)
    return AppearanceProfile(**data)


def hairstyle_catalog() -> dict[str, Any]:
    return {
        "hairstyles": list(_HAIRSTYLE_CATALOG),
        "hair_colors": list(_HAIR_COLORS),
        "beard_styles": list(_BEARD_STYLES),
    }
