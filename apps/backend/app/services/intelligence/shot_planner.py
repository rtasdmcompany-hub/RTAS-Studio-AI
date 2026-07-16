"""Module 5 — Shot Planner."""

from __future__ import annotations

from app.services.intelligence.models import CameraPlan, ScenePlan, ShotPlan


def plan_shots(
    scenes: list[ScenePlan],
    cameras: list[CameraPlan],
) -> list[ShotPlan]:
    cam_by_scene = {c.scene_index: c for c in cameras}
    shots: list[ShotPlan] = []

    for scene in scenes:
        cam = cam_by_scene.get(scene.index)
        cam_dict = cam.to_dict() if cam else {}
        # Two production-ready shots per scene.
        split_a = max(1, scene.duration_seconds // 2)
        split_b = max(1, scene.duration_seconds - split_a)
        for shot_index, (dur, action) in enumerate(
            (
                (split_a, scene.actions[0] if scene.actions else "establish"),
                (split_b, scene.actions[-1] if scene.actions else "payoff"),
            )
        ):
            shots.append(
                ShotPlan(
                    scene_index=scene.index,
                    shot_index=shot_index,
                    title=f"{scene.title} — shot {shot_index + 1}",
                    duration_seconds=dur,
                    description=scene.description,
                    camera=cam_dict,
                    action=action,
                    dialogue_hint=None,
                )
            )
    return shots
