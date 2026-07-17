"""Character templates and identity builders."""

from __future__ import annotations

import hashlib
import time
from typing import Any

from app.services.character_generation.models import (
    CharacterDNA,
    CharacterIdentity,
    CharacterTemplate,
)
from app.services.character_generation.version import ENGINE_VERSION

TEMPLATES: dict[str, CharacterTemplate] = {
    "cinematic_lead": CharacterTemplate(
        template_id="cinematic_lead",
        name="Cinematic Lead",
        description="Hero / lead character for narrative productions",
        defaults={
            "gender": "female",
            "age": 28,
            "ethnicity": "south_asian",
            "body_type": "athletic",
            "hairstyle": "long_wavy",
            "beard": "none",
            "skin": "medium_warm",
            "eye_color": "brown",
            "clothing": "cinematic_jacket",
            "accessories": ["earrings"],
        },
    ),
    "supporting_actor": CharacterTemplate(
        template_id="supporting_actor",
        name="Supporting Actor",
        description="Supporting cast template",
        defaults={
            "gender": "male",
            "age": 35,
            "ethnicity": "mixed",
            "body_type": "average",
            "hairstyle": "short_textured",
            "beard": "light_stubble",
            "skin": "olive",
            "eye_color": "hazel",
            "clothing": "casual_shirt",
            "accessories": ["watch"],
        },
    ),
    "narrator_presence": CharacterTemplate(
        template_id="narrator_presence",
        name="Narrator Presence",
        description="On-camera narrator / presenter",
        defaults={
            "gender": "non_binary",
            "age": 30,
            "ethnicity": "east_asian",
            "body_type": "slim",
            "hairstyle": "bob",
            "beard": "none",
            "skin": "fair",
            "eye_color": "dark_brown",
            "clothing": "studio_blazer",
            "accessories": ["glasses"],
        },
    ),
}


def list_templates() -> list[CharacterTemplate]:
    return list(TEMPLATES.values())


def get_template(template_id: str | None) -> CharacterTemplate:
    if template_id and template_id in TEMPLATES:
        return TEMPLATES[template_id]
    return TEMPLATES["cinematic_lead"]


def _fingerprint(identity: CharacterIdentity) -> str:
    payload = (
        f"{identity.gender}|{identity.age}|{identity.ethnicity}|{identity.body_type}|"
        f"{identity.hairstyle}|{identity.beard}|{identity.skin}|{identity.eye_color}|"
        f"{identity.clothing}|{','.join(identity.accessories)}"
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:24]


def build_identity(
    *,
    unique_id: str,
    overrides: dict[str, Any] | None = None,
    template_id: str | None = None,
) -> CharacterIdentity:
    tmpl = get_template(template_id)
    base = dict(tmpl.defaults)
    if overrides:
        for key, value in overrides.items():
            if value is not None and key in (
                "gender",
                "age",
                "ethnicity",
                "body_type",
                "hairstyle",
                "beard",
                "skin",
                "eye_color",
                "clothing",
                "accessories",
            ):
                base[key] = value
    accessories = base.get("accessories") or []
    if isinstance(accessories, str):
        accessories = [a.strip() for a in accessories.split(",") if a.strip()]
    age = int(base.get("age") or 28)
    age = max(1, min(120, age))
    return CharacterIdentity(
        unique_id=unique_id,
        version=ENGINE_VERSION,
        gender=str(base.get("gender") or "unspecified"),
        age=age,
        ethnicity=str(base.get("ethnicity") or "unspecified"),
        body_type=str(base.get("body_type") or "average"),
        hairstyle=str(base.get("hairstyle") or "short"),
        beard=str(base.get("beard") or "none"),
        skin=str(base.get("skin") or "medium"),
        eye_color=str(base.get("eye_color") or "brown"),
        clothing=str(base.get("clothing") or "neutral"),
        accessories=list(accessories),
    )


def build_dna(
    character_id: str,
    identity: CharacterIdentity,
    *,
    version: int = 1,
    traits: dict[str, Any] | None = None,
) -> CharacterDNA:
    now = time.time()
    dna_id = f"dna_{hashlib.sha1(f'{character_id}|{identity.unique_id}'.encode()).hexdigest()[:12]}"
    return CharacterDNA(
        dna_id=dna_id,
        character_id=character_id,
        version=version,
        identity=identity,
        traits=traits or {"consistency_lock": True, "engine": ENGINE_VERSION},
        fingerprint=_fingerprint(identity),
        locked=True,
        created_at=now,
        updated_at=now,
    )
