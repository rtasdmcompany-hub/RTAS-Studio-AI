"""Automatic correction of scenes/shots/prompts to restore identity consistency."""

from __future__ import annotations

from app.services.intelligence.character_consistency.models import (
    CorrectionAction,
    IdentityProfile,
    VerificationResult,
)
from app.services.intelligence.models import ScenePlan, ShotPlan


def build_identity_lock_block(profiles: list[IdentityProfile]) -> str:
    if not profiles:
        return "IDENTITY LOCK: maintain consistent subject identity across all scenes."
    return " ".join(p.lock_prompt() for p in profiles)


def apply_automatic_corrections(
    *,
    profiles: list[IdentityProfile],
    scenes: list[ScenePlan],
    shots: list[ShotPlan],
    verification: VerificationResult,
    enhanced_prompt: str,
) -> tuple[list[ScenePlan], list[ShotPlan], str, list[CorrectionAction]]:
    lock = build_identity_lock_block(profiles)
    ids = [p.subject_id for p in profiles] or ["Character_A"]
    corrections: list[CorrectionAction] = []

    # Always reinforce prompt lock.
    if lock and lock not in enhanced_prompt:
        before = enhanced_prompt
        enhanced_prompt = f"{enhanced_prompt} {lock}".strip()
        corrections.append(
            CorrectionAction(
                target="prompt",
                index=None,
                field="enhanced_prompt",
                before=before[:180],
                after=enhanced_prompt[:180],
                reason="inject_identity_lock_block",
            )
        )

    # Forbid drift language
    forbid = (
        " Do not change face, hair, age, body, clothes, or identity between shots."
        " No face swapping. No clothing drift. Match locked expression family."
    )
    if "no face swapping" not in enhanced_prompt.lower():
        enhanced_prompt = f"{enhanced_prompt}{forbid}".strip()
        corrections.append(
            CorrectionAction(
                target="prompt",
                index=None,
                field="enhanced_prompt",
                before="(append)",
                after=forbid.strip(),
                reason="prevent_identity_drift_rules",
            )
        )

    new_scenes: list[ScenePlan] = []
    for scene in scenes:
        desc = scene.description or ""
        before = desc
        if "identity lock" not in desc.lower():
            desc = f"{desc} | {lock}".strip(" |")
        # Align characters list
        chars = list(ids)
        if desc != before or scene.characters != chars:
            corrections.append(
                CorrectionAction(
                    target="scene",
                    index=scene.index,
                    field="description/characters",
                    before=before[:120],
                    after=desc[:120],
                    reason="scene_identity_alignment",
                )
            )
        new_scenes.append(
            ScenePlan(
                index=scene.index,
                title=scene.title,
                duration_seconds=scene.duration_seconds,
                description=desc,
                environment=scene.environment,
                characters=chars,
                actions=scene.actions,
                transitions=scene.transitions,
            )
        )

    primary_expr = profiles[0].expression if profiles else "natural cinematic expression"
    new_shots: list[ShotPlan] = []
    for shot in shots:
        camera = dict(shot.camera or {})
        camera["character_ids"] = ids
        camera["identity_lock"] = True
        camera["face_embedding_refs"] = [
            p.face_embedding_ref for p in profiles if p.face_embedding_ref
        ]
        camera["locked_expression"] = primary_expr
        desc = shot.description or ""
        before = desc
        if "identity lock" not in desc.lower():
            desc = f"{desc} | {lock}".strip(" |")
        # Emotion mismatch correction: soften conflicting action text
        action = shot.action or ""
        for drift in verification.drifts:
            if (
                drift.kind == "emotion_mismatch"
                and drift.scene_index == shot.scene_index
                and drift.shot_index == shot.shot_index
            ):
                action = f"{action}; expression={primary_expr}"
                corrections.append(
                    CorrectionAction(
                        target="shot",
                        index=shot.shot_index,
                        field="action",
                        before=shot.action or "",
                        after=action,
                        reason="emotion_mismatch_correction",
                    )
                )
        if desc != before:
            corrections.append(
                CorrectionAction(
                    target="shot",
                    index=shot.shot_index,
                    field="description",
                    before=before[:120],
                    after=desc[:120],
                    reason="shot_identity_lock",
                )
            )
        new_shots.append(
            ShotPlan(
                scene_index=shot.scene_index,
                shot_index=shot.shot_index,
                title=shot.title,
                duration_seconds=shot.duration_seconds,
                description=desc,
                camera=camera,
                action=action,
                dialogue_hint=shot.dialogue_hint,
            )
        )

    # If score was low due to missing locks, corrections above address it.
    _ = verification
    return new_scenes, new_shots, enhanced_prompt, corrections
