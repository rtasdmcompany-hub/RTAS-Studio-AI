"""Module 2 — Consistency Engine (identity lock across scenes/shots)."""

from __future__ import annotations

from app.services.intelligence.director_models import (
    CharacterMemory,
    ConsistencyReport,
)
from app.services.intelligence.models import ScenePlan, ShotPlan


def build_consistency_report(
    characters: list[CharacterMemory],
    *,
    user_allows_wardrobe_change: bool = False,
) -> ConsistencyReport:
    ids = [c.character_id for c in characters]
    notes = [
        "Reuse identical face, hair, clothing, body, and proportions unless user overrides.",
    ]
    if user_allows_wardrobe_change:
        notes.append("User override enabled: wardrobe may change between scenes.")
    else:
        notes.append("Wardrobe locked for full timeline.")

    for c in characters:
        notes.append(c.identity_lock_prompt())

    return ConsistencyReport(
        locked_character_ids=ids,
        face_locked=True,
        hair_locked=True,
        clothing_locked=not user_allows_wardrobe_change,
        body_locked=True,
        proportions_locked=True,
        overrides_allowed=user_allows_wardrobe_change,
        notes=notes,
    )


def apply_consistency_to_scenes(
    scenes: list[ScenePlan],
    characters: list[CharacterMemory],
) -> list[ScenePlan]:
    """Ensure every scene references the same character IDs."""
    ids = [c.character_id for c in characters] or ["Character_A"]
    updated: list[ScenePlan] = []
    for scene in scenes:
        updated.append(
            ScenePlan(
                index=scene.index,
                title=scene.title,
                duration_seconds=scene.duration_seconds,
                description=scene.description
                + " | "
                + " ".join(c.identity_lock_prompt() for c in characters),
                environment=scene.environment,
                characters=ids,
                actions=scene.actions,
                transitions=scene.transitions,
            )
        )
    return updated


def apply_consistency_to_shots(
    shots: list[ShotPlan],
    characters: list[CharacterMemory],
) -> list[ShotPlan]:
    ids = [c.character_id for c in characters] or ["Character_A"]
    lock = " ".join(c.identity_lock_prompt() for c in characters)
    updated: list[ShotPlan] = []
    for shot in shots:
        camera = dict(shot.camera or {})
        camera["character_ids"] = ids
        camera["identity_lock"] = True
        updated.append(
            ShotPlan(
                scene_index=shot.scene_index,
                shot_index=shot.shot_index,
                title=shot.title,
                duration_seconds=shot.duration_seconds,
                description=f"{shot.description} | {lock}",
                camera=camera,
                action=shot.action,
                dialogue_hint=shot.dialogue_hint,
            )
        )
    return updated
