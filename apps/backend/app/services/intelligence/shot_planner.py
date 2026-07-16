"""Module 5 — Shot Planner (delegates to Scene Breakdown Engine)."""

from __future__ import annotations

from app.services.intelligence.models import CameraPlan, ScenePlan, ShotPlan


def plan_shots(
    scenes: list[ScenePlan],
    cameras: list[CameraPlan],
) -> list[ShotPlan]:
    """
    Legacy helper kept for compatibility.

    Prefer `scene_breakdown.build_production_breakdown` via the pipeline.
    When only legacy scene/camera plans exist, synthesize one shot per scene.
    """
    cam_by_scene = {c.scene_index: c for c in cameras}
    shots: list[ShotPlan] = []
    for scene in scenes:
        cam = cam_by_scene.get(scene.index)
        cam_dict = cam.to_dict() if cam else {}
        shots.append(
            ShotPlan(
                scene_index=scene.index,
                shot_index=0,
                title=f"{scene.title} — primary",
                duration_seconds=max(1, scene.duration_seconds),
                description=scene.description,
                camera=cam_dict,
                action=scene.actions[0] if scene.actions else "cover",
                dialogue_hint=None,
            )
        )
    return shots
