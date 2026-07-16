"""Module 4 — Camera Planner."""

from __future__ import annotations

from app.services.intelligence.models import CameraPlan, PromptIntelligenceResult, ScenePlan


def plan_cameras(
    scenes: list[ScenePlan],
    intelligence: PromptIntelligenceResult,
) -> list[CameraPlan]:
    movement_cycle = (
        "slow push-in",
        "lateral track",
        "static locked-off",
        "gentle orbit",
    )
    framing_cycle = ("wide", "medium", "close-up", "medium-wide")
    angle_cycle = ("eye-level", "low angle", "eye-level", "slight high angle")

    plans: list[CameraPlan] = []
    for i, scene in enumerate(scenes):
        plans.append(
            CameraPlan(
                scene_index=scene.index,
                lens="spherical cinema prime",
                focal_length_mm=35 if i == 0 else 50 if i % 2 else 85,
                movement=movement_cycle[i % len(movement_cycle)],
                framing=framing_cycle[i % len(framing_cycle)],
                angle=angle_cycle[i % len(angle_cycle)],
                depth="shallow DOF" if intelligence.style == "real" else "readable mid DOF",
                cinematic_motion=(
                    intelligence.camera_requirements[0]
                    if intelligence.camera_requirements
                    else "smooth cinematic motion"
                ),
            )
        )
    return plans
