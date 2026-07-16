"""
Bridge Scene Breakdown → legacy ScenePlan / CameraPlan / ShotPlan.

Keeps Character Memory, Director Engine, Story Continuity, and Production
Package contracts intact.
"""

from __future__ import annotations

from app.services.intelligence.models import CameraPlan, ScenePlan, ShotPlan
from app.services.intelligence.scene_breakdown.models import ProductionBreakdown


def to_legacy_plans(
    breakdown: ProductionBreakdown,
) -> tuple[list[ScenePlan], list[CameraPlan], list[ShotPlan]]:
    scenes: list[ScenePlan] = []
    cameras: list[CameraPlan] = []
    shots: list[ShotPlan] = []

    for scene in breakdown.scenes:
        idx = scene.scene_number - 1
        primary = scene.shots[0] if scene.shots else None
        scenes.append(
            ScenePlan(
                index=idx,
                title=scene.title,
                duration_seconds=max(1, int(round(scene.estimated_duration_seconds))),
                description=scene.scene_purpose,
                environment=scene.environment,
                characters=["lead subject"],
                actions=[
                    scene.scene_purpose,
                    scene.character_emotion,
                ],
                transitions=scene.transition_type,
            )
        )
        if primary:
            focal = 35
            lens = primary.lens.lower()
            if "85" in lens:
                focal = 85
            elif "50" in lens:
                focal = 50
            elif "24" in lens or "macro" in lens:
                focal = 24 if "24" in lens else 100
            cameras.append(
                CameraPlan(
                    scene_index=idx,
                    lens=primary.lens,
                    focal_length_mm=focal,
                    movement=primary.camera_movement,
                    framing=primary.shot_type,
                    angle=primary.camera_angle,
                    depth=primary.depth_of_field,
                    cinematic_motion=primary.camera_movement,
                )
            )
        for shot in scene.shots:
            shots.append(
                ShotPlan(
                    scene_index=idx,
                    shot_index=shot.shot_number - 1,
                    title=f"{scene.title} — {shot.shot_type}",
                    duration_seconds=max(
                        1, int(round(shot.estimated_duration_seconds))
                    ),
                    description=shot.purpose or scene.scene_purpose,
                    camera={
                        "shot_type": shot.shot_type,
                        "camera_angle": shot.camera_angle,
                        "lens": shot.lens,
                        "camera_movement": shot.camera_movement,
                        "lighting": shot.lighting,
                        "depth_of_field": shot.depth_of_field,
                        "composition": shot.composition,
                        "color_palette": shot.color_palette,
                    },
                    action=shot.purpose or scene.character_emotion,
                    dialogue_hint=None,
                )
            )

    return scenes, cameras, shots
