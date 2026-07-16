"""
Character Consistency Engine.

Maintains exact subject identity across every scene/shot.
Integrates Character Memory, Prompt Understanding, Scene/Shot plans.
"""

from __future__ import annotations

from typing import Any

from app.services.intelligence.character_consistency.corrector import (
    apply_automatic_corrections,
    build_identity_lock_block,
)
from app.services.intelligence.character_consistency.identity_builder import (
    build_identity_profiles,
)
from app.services.intelligence.character_consistency.models import (
    CharacterConsistencyResult,
)
from app.services.intelligence.character_consistency.verifier import (
    verify_identity_consistency,
)
from app.services.intelligence.director_models import CharacterMemory
from app.services.intelligence.models import ScenePlan, ShotPlan


def run_character_consistency(
    *,
    prompt: str,
    characters: list[CharacterMemory],
    scenes: list[ScenePlan],
    shots: list[ShotPlan],
    enhanced_prompt: str = "",
    understanding: dict[str, Any] | None = None,
    emotion_hint: str | None = None,
    pass_threshold: float = 0.72,
) -> tuple[CharacterConsistencyResult, list[ScenePlan], list[ShotPlan], str]:
    kind, profiles = build_identity_profiles(
        prompt=prompt,
        characters=characters,
        understanding=understanding,
        emotion_hint=emotion_hint,
    )

    # First verification pass (may find missing locks).
    verification = verify_identity_consistency(
        profiles=profiles,
        scenes=scenes,
        shots=shots,
        understanding=understanding,
        pass_threshold=pass_threshold,
    )

    scenes2, shots2, prompt2, corrections = apply_automatic_corrections(
        profiles=profiles,
        scenes=scenes,
        shots=shots,
        verification=verification,
        enhanced_prompt=enhanced_prompt or prompt,
    )

    # Re-verify after automatic correction.
    verification2 = verify_identity_consistency(
        profiles=profiles,
        scenes=scenes2,
        shots=shots2,
        understanding=understanding,
        pass_threshold=pass_threshold,
    )

    result = CharacterConsistencyResult(
        subject_kind=kind,
        profiles=profiles,
        verification=verification2,
        corrections=corrections,
        identity_lock_block=build_identity_lock_block(profiles),
        embedding_ready=all(bool(p.face_embedding) for p in profiles),
    )
    return result, scenes2, shots2, prompt2


def run_character_consistency_dict(**kwargs: Any) -> dict[str, Any]:
    result, scenes, shots, prompt = run_character_consistency(**kwargs)
    return {
        **result.to_dict(),
        "scenes": [s.to_dict() for s in scenes],
        "shots": [s.to_dict() for s in shots],
        "enhanced_prompt": prompt,
    }
