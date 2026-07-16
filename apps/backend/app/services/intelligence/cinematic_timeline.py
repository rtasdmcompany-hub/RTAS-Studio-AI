"""Module 5 — Cinematic Timeline generator."""

from __future__ import annotations

from app.services.intelligence.director_models import (
    CharacterMemory,
    CinematicTimeline,
    DirectorPlan,
    TimelineNode,
)
from app.services.intelligence.models import ScenePlan, ShotPlan


def build_cinematic_timeline(
    scenes: list[ScenePlan],
    shots: list[ShotPlan],
    characters: list[CharacterMemory],
    director: DirectorPlan,
) -> CinematicTimeline:
    nodes: list[TimelineNode] = []
    char_ids = [c.character_id for c in characters]
    decision_idx = 0

    for scene in scenes:
        scene_id = f"scene_{scene.index + 1}"
        nodes.append(
            TimelineNode(
                kind="scene",
                id=scene_id,
                label=scene.title,
                duration_seconds=scene.duration_seconds,
                character_ids=char_ids,
                metadata={"environment": scene.environment},
            )
        )

        scene_shots = [s for s in shots if s.scene_index == scene.index]
        for shot in scene_shots:
            decision = (
                director.decisions[decision_idx]
                if decision_idx < len(director.decisions)
                else None
            )
            decision_idx += 1
            shot_id = f"{scene_id}_shot_{shot.shot_index + 1}"
            nodes.append(
                TimelineNode(
                    kind="shot",
                    id=shot_id,
                    label=shot.title,
                    duration_seconds=shot.duration_seconds,
                    parent_id=scene_id,
                    character_ids=char_ids,
                    metadata={
                        "action": shot.action,
                        "shot_type": decision.shot_type if decision else "Medium Shot",
                        "pacing": decision.pacing if decision else "steady",
                    },
                )
            )

        # Transition after scene (except final).
        if scene.index < len(scenes) - 1:
            nodes.append(
                TimelineNode(
                    kind="transition",
                    id=f"transition_after_{scene_id}",
                    label=scene.transitions or "cut",
                    duration_seconds=0,
                    parent_id=scene_id,
                    character_ids=char_ids,
                    metadata={"style": director.transition_style},
                )
            )

    total = sum(n.duration_seconds for n in nodes if n.kind == "shot")
    if total <= 0:
        total = sum(s.duration_seconds for s in scenes)

    return CinematicTimeline(nodes=nodes, total_duration_seconds=total)
