"""Request validation for character generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

_VALID_SLOTS = {"Character_A", "Character_B", "Character_C", "A", "B", "C"}


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    name: str | None = None
    template_id: str | None = None
    registry_slot: str | None = None
    overrides: dict[str, Any] = field(default_factory=dict)


def _normalize_slot(slot: str | None) -> str | None:
    if not slot:
        return None
    s = slot.strip()
    aliases = {"A": "Character_A", "B": "Character_B", "C": "Character_C"}
    if s in aliases:
        return aliases[s]
    if s in ("Character_A", "Character_B", "Character_C"):
        return s
    return None


def validate_create_request(
    *,
    name: str | None = None,
    prompt: str | None = None,
    template_id: str | None = None,
    registry_slot: str | None = None,
    gender: str | None = None,
    age: int | None = None,
    ethnicity: str | None = None,
    body_type: str | None = None,
    hairstyle: str | None = None,
    beard: str | None = None,
    skin: str | None = None,
    eye_color: str | None = None,
    clothing: str | None = None,
    accessories: list[str] | None = None,
) -> ValidationResult:
    errors: list[str] = []
    if registry_slot and registry_slot not in _VALID_SLOTS:
        errors.append("registry_slot must be Character_A, Character_B, or Character_C")
    if age is not None and (age < 1 or age > 120):
        errors.append("age must be between 1 and 120")
    if prompt is not None and len(prompt) > 8000:
        errors.append("prompt too long")

    overrides: dict[str, Any] = {}
    for key, value in {
        "gender": gender,
        "age": age,
        "ethnicity": ethnicity,
        "body_type": body_type,
        "hairstyle": hairstyle,
        "beard": beard,
        "skin": skin,
        "eye_color": eye_color,
        "clothing": clothing,
        "accessories": accessories,
    }.items():
        if value is not None:
            overrides[key] = value

    return ValidationResult(
        ok=len(errors) == 0,
        errors=errors,
        name=(name or "").strip() or None,
        template_id=template_id,
        registry_slot=_normalize_slot(registry_slot),
        overrides=overrides,
    )
