"""Module 3 — AI Director (shot order, pacing, cinematic decisions)."""

from __future__ import annotations

from app.services.intelligence.director_models import DirectorDecision, DirectorPlan
from app.services.intelligence.models import (
    PromptIntelligenceResult,
    ScenePlan,
    ShotPlan,
)

_SHOT_TYPES = (
    "Wide Shot",
    "Close Up",
    "Over Shoulder",
    "Tracking",
    "Reveal",
    "POV",
    "Drone",
    "Medium Shot",
)

_TRANSITIONS = ("cut", "match cut", "dissolve", "whip pan", "fade")


def direct_production(
    scenes: list[ScenePlan],
    shots: list[ShotPlan],
    intelligence: PromptIntelligenceResult,
) -> DirectorPlan:
    decisions: list[DirectorDecision] = []
    shot_order: list[str] = []
    emotional_pacing: list[str] = []
    scene_emphasis: list[str] = []
    timing_notes: list[str] = []

    emotion = intelligence.emotion
    for i, scene in enumerate(scenes):
        scene_shots = [s for s in shots if s.scene_index == scene.index]
        emphasis = (
            "character reveal"
            if i == 0
            else "emotional peak"
            if i == len(scenes) // 2
            else "resolution"
        )
        scene_emphasis.append(f"Scene {scene.index + 1}: {emphasis}")

        for j, shot in enumerate(scene_shots):
            # Director chooses shot grammar by beat position.
            if j == 0 and i == 0:
                shot_type = "Wide Shot"
            elif j == 0:
                shot_type = "Reveal"
            elif emotion in ("dramatic", "somber") and j == len(scene_shots) - 1:
                shot_type = "Close Up"
            elif "drone" in " ".join(intelligence.camera_requirements).lower():
                shot_type = "Drone"
            else:
                shot_type = _SHOT_TYPES[(i + j) % len(_SHOT_TYPES)]

            pacing = "slow" if emotion in ("calm", "somber") else "building"
            if i == len(scenes) - 1:
                pacing = "resolve"

            transition_in = _TRANSITIONS[i % len(_TRANSITIONS)] if j == 0 else "cut"
            transition_out = (
                scene.transitions
                if j == len(scene_shots) - 1
                else "cut"
            )

            node_id = f"S{scene.index + 1}.SH{shot.shot_index + 1}"
            shot_order.append(f"{node_id}:{shot_type}")
            emotional_pacing.append(f"{node_id}:{emotion}/{pacing}")
            timing_notes.append(
                f"{node_id} hold {shot.duration_seconds}s — {emphasis}"
            )

            decisions.append(
                DirectorDecision(
                    shot_type=shot_type,
                    emotional_beat=emotion,
                    emphasis=emphasis,
                    transition_in=transition_in,
                    transition_out=transition_out,
                    pacing=pacing,
                    dramatic_timing=f"{shot.duration_seconds}s beat",
                )
            )

    rhythm = (
        "contemplative"
        if emotion in ("calm", "somber")
        else "dynamic commercial"
        if intelligence.cinematic_genre == "commercial"
        else "narrative rise-fall"
    )

    notes = [
        "Direct for identity-locked continuity across all shots.",
        f"Primary emotion: {emotion}.",
        f"Genre rhythm: {rhythm}.",
        "Prefer motivated camera moves over random motion.",
        "Protect hero face likeness in every close-up.",
    ]

    return DirectorPlan(
        shot_order=shot_order,
        emotional_pacing=emotional_pacing,
        cinematic_rhythm=rhythm,
        transition_style="motivated editorial",
        dramatic_timing_notes=timing_notes,
        scene_emphasis=scene_emphasis,
        decisions=decisions,
        director_notes=notes,
    )
