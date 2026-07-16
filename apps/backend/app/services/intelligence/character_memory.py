"""Module 1 — Character Memory Engine."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from app.services.intelligence.director_models import CharacterMemory

_GENDER_HINTS = (
    ("woman", "female"),
    ("female", "female"),
    ("girl", "female"),
    ("man", "male"),
    ("male", "male"),
    ("boy", "male"),
)

_HAIR_HINTS = (
    ("long hair", "long"),
    ("short hair", "short"),
    ("bald", "bald"),
    ("curly", "curly"),
    ("straight hair", "straight"),
    ("black hair", "black"),
    ("brown hair", "brown"),
    ("blonde", "blonde"),
)

_BEARD_HINTS = (
    ("beard", "full beard"),
    ("stubble", "stubble"),
    ("clean shaven", "none"),
    ("clean-shaven", "none"),
)

_SKIN_HINTS = (
    ("fair skin", "fair"),
    ("dark skin", "deep"),
    ("brown skin", "medium-brown"),
    ("olive skin", "olive"),
)

_OUTFIT_HINTS = (
    ("suit", "business suit"),
    ("hoodie", "casual hoodie"),
    ("traditional", "traditional attire"),
    ("uniform", "uniform"),
    ("dress", "dress"),
)


def _pick(text: str, table: tuple[tuple[str, str], ...], default: str) -> str:
    for key, value in table:
        if key in text:
            return value
    return default


def _character_id(index: int, seed: str) -> str:
    letter = chr(ord("A") + min(index, 25))
    digest = hashlib.sha1(f"{seed}:{index}".encode("utf-8")).hexdigest()[:6]
    return f"Character_{letter}_{digest}"


def build_character_memories(
    prompt: str,
    *,
    style_hint: str | None = None,
    reference_image_urls: list[str] | None = None,
    character_count_hint: int | None = None,
) -> list[CharacterMemory]:
    """Assign Character_A / Character_B… with locked identity traits."""
    lower = (prompt or "").lower()
    refs = list(reference_image_urls or [])

    # Detect multiple characters from prompt cues.
    count = character_count_hint or 1
    if re.search(r"\b(two|both|pair|duo|couple)\b", lower):
        count = max(count, 2)
    if re.search(r"\b(three|trio|family)\b", lower):
        count = max(count, 3)
    if re.search(r"\b(crowd|audience|many people)\b", lower):
        count = max(count, 3)
    if "characters" in lower and count < 2:
        count = 2
    has_male = bool(re.search(r"\b(man|male|boy|gentleman)\b", lower))
    has_female = bool(re.search(r"\b(woman|female|girl|lady)\b", lower))
    if has_male and has_female:
        count = max(count, 2)
    if re.search(r"\b(and|&)\b", lower) and (
        lower.count("person") >= 2 or lower.count("character") >= 2
    ):
        count = max(count, 2)
    # Animals / vehicles still get a single primary subject track by default.
    if re.search(r"\b(dog|cat|horse|animal|lion|pet)\b", lower) and count < 1:
        count = 1
    if re.search(r"\b(car|truck|vehicle|motorcycle)\b", lower) and count < 1:
        count = 1
    count = max(1, min(count, 4))

    memories: list[CharacterMemory] = []
    for i in range(count):
        cid = _character_id(i, prompt or "rtas")
        gender = _pick(lower, _GENDER_HINTS, "unspecified")
        hair = _pick(lower, _HAIR_HINTS, "natural")
        beard = _pick(lower, _BEARD_HINTS, "none" if gender == "female" else "none")
        skin = _pick(lower, _SKIN_HINTS, "natural")
        if "pakistani" in lower or "south asian" in lower or "indian" in lower:
            skin = "medium-brown"
        outfit = _pick(lower, _OUTFIT_HINTS, "wardrobe consistent with scene")
        age = "adult"
        if "child" in lower or "kid" in lower:
            age = "child"
        elif "elderly" in lower or "old" in lower:
            age = "elder"
        elif "teen" in lower:
            age = "teen"

        face_shape = "oval"
        eye_color = "brown"
        accessories: list[str] = []
        if "glasses" in lower:
            accessories.append("glasses")
        if "hat" in lower:
            accessories.append("hat")

        # First character gets primary face reference when provided.
        char_refs = [refs[i]] if i < len(refs) else ([refs[0]] if refs and i == 0 else [])
        embedding_ref = f"embedding://pending/{cid}" if char_refs or style_hint == "real" else None

        memories.append(
            CharacterMemory(
                character_id=cid,
                gender=gender,
                age=age,
                hair=hair,
                beard=beard,
                skin_tone=skin,
                face_shape=face_shape,
                eye_color=eye_color,
                outfit=outfit,
                accessories=accessories,
                reference_image_urls=char_refs,
                face_embedding_ref=embedding_ref,
                locked_traits=[
                    "face",
                    "hairstyle",
                    "clothing",
                    "body",
                    "proportions",
                ],
            )
        )
    return memories


def character_memory_dicts(
    prompt: str, **kwargs: Any
) -> list[dict[str, Any]]:
    return [m.to_dict() for m in build_character_memories(prompt, **kwargs)]
