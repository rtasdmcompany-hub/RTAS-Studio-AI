"""Reference Face Lock — Character Memory + face reference integration."""

from __future__ import annotations

from typing import Any

from app.services.talking_avatar.models import FaceLock


def build_face_lock(
    character_memory: list[dict[str, Any]] | None,
    *,
    reference_face_url: str | None = None,
    identity_strength: float = 0.9,
) -> FaceLock:
    chars = list(character_memory or [])
    lead = chars[0] if chars else {}
    character_id = str(lead.get("character_id") or "Avatar_Lead")

    ref = reference_face_url
    if not ref:
        refs = lead.get("reference_image_urls") or []
        if refs and isinstance(refs[0], str):
            ref = refs[0].strip() or None

    locked_traits = list(lead.get("locked_traits") or [])
    if not locked_traits:
        locked_traits = [
            "face",
            "hair",
            "skin_tone",
            "eye_color",
            "outfit",
        ]

    notes = [
        "Reference face lock active for talking avatar",
        "No face morphing / identity drift across timeline",
    ]
    if lead.get("outfit"):
        notes.append(f"Wardrobe lock: {lead.get('outfit')}")

    return FaceLock(
        character_id=character_id,
        reference_face_url=ref,
        face_locked=True,
        identity_strength=max(0.5, min(1.0, float(identity_strength))),
        locked_traits=locked_traits,
        notes=notes,
    )


def face_lock_prompt(face_lock: FaceLock, character: dict[str, Any] | None = None) -> str:
    c = character or {}
    parts = [
        f"REFERENCE FACE LOCK [{face_lock.character_id}]:",
        f"identity_strength={face_lock.identity_strength:.2f}.",
        "Exact facial identity from reference; photoreal skin; stable likeness.",
    ]
    if c.get("hair"):
        parts.append(f"hair={c.get('hair')}.")
    if c.get("eye_color"):
        parts.append(f"eyes={c.get('eye_color')}.")
    if c.get("outfit"):
        parts.append(f"outfit={c.get('outfit')}.")
    parts.append("Traits locked: " + ", ".join(face_lock.locked_traits) + ".")
    return " ".join(parts)
