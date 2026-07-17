"""Accessories Manager — wearable extras without identity drift."""

from __future__ import annotations

from typing import Any

from app.services.appearance.models import AppearanceProfile

_ACCESSORY_CATALOG = (
    "watch",
    "glasses",
    "sunglasses",
    "earrings",
    "necklace",
    "bracelet",
    "hat",
    "scarf",
    "cufflinks",
    "statement_jewelry",
    "fitness_band",
    "heritage_accessory",
    "briefcase_strap",
)


def normalize_accessories(items: list[str] | None) -> list[str]:
    if not items:
        return []
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in items:
        token = str(raw or "").strip().lower().replace(" ", "_")
        if token and token not in seen:
            seen.add(token)
            cleaned.append(token)
    return cleaned[:20]


def apply_accessories(
    profile: AppearanceProfile,
    accessories: list[str] | None,
    *,
    replace: bool = True,
) -> AppearanceProfile:
    data = profile.to_dict()
    incoming = normalize_accessories(accessories)
    if replace:
        data["accessories"] = incoming
    else:
        data["accessories"] = normalize_accessories(
            list(profile.accessories) + incoming
        )
    return AppearanceProfile(**data)


def accessories_catalog() -> dict[str, Any]:
    return {"accessories": list(_ACCESSORY_CATALOG)}
