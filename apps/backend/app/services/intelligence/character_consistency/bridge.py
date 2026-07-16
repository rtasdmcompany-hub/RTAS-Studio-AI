"""Bridge IdentityProfiles → CharacterMemory / ConsistencyReport."""

from __future__ import annotations

from app.services.intelligence.character_consistency.models import IdentityProfile
from app.services.intelligence.director_models import CharacterMemory, ConsistencyReport


def enrich_character_memories(
    characters: list[CharacterMemory],
    profiles: list[IdentityProfile],
) -> list[CharacterMemory]:
    by_id = {p.subject_id: p for p in profiles}
    enriched: list[CharacterMemory] = []
    for mem in characters:
        profile = by_id.get(mem.character_id)
        if not profile:
            enriched.append(mem)
            continue
        enriched.append(
            CharacterMemory(
                character_id=mem.character_id,
                gender=mem.gender,
                age=profile.age or mem.age,
                hair=profile.hair if profile.hair != "n/a" else mem.hair,
                beard=mem.beard,
                skin_tone=profile.skin_tone or mem.skin_tone,
                face_shape=mem.face_shape,
                eye_color=profile.eye_color or mem.eye_color,
                outfit=profile.clothes if profile.clothes != "n/a" else mem.outfit,
                accessories=list(profile.accessories or mem.accessories),
                reference_image_urls=list(
                    profile.reference_image_urls or mem.reference_image_urls
                ),
                face_embedding_ref=profile.face_embedding_ref or mem.face_embedding_ref,
                locked_traits=list(profile.locked_traits or mem.locked_traits),
            )
        )
    return enriched


def consistency_report_from_profiles(
    profiles: list[IdentityProfile],
    *,
    user_allows_wardrobe_change: bool = False,
) -> ConsistencyReport:
    return ConsistencyReport(
        locked_character_ids=[p.subject_id for p in profiles],
        face_locked=True,
        hair_locked=True,
        clothing_locked=not user_allows_wardrobe_change,
        body_locked=True,
        proportions_locked=True,
        overrides_allowed=user_allows_wardrobe_change,
        notes=[p.lock_prompt() for p in profiles]
        + [
            "Prevent face swapping, hair changes, clothing drift, identity drift.",
            "Match locked expression / walking style / voice across scenes.",
        ],
    )
