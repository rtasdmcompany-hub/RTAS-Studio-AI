"""Cinematic pacing — scene count, shot count, durations, rhythm."""

from __future__ import annotations

from dataclasses import dataclass

from app.services.intelligence.models import PromptIntelligenceResult
from app.services.intelligence.prompt_understanding.models import (
    CinematicPromptUnderstanding,
)


@dataclass(frozen=True)
class PacingPlan:
    target_runtime: float
    scene_count: int
    shots_per_scene: int
    story_rhythm: str
    notes: list[str]


def plan_pacing(
    *,
    understanding: CinematicPromptUnderstanding,
    intelligence: PromptIntelligenceResult,
    beat_count: int,
) -> PacingPlan:
    base = float(intelligence.estimated_duration_seconds or 15)
    category = understanding.category

    if category in ("TikTok", "YouTube Shorts", "Instagram Reel"):
        target = min(base, 30.0) if base else 15.0
        rhythm = "hook → punch → payoff"
        notes = ["Vertical social pacing", "Front-load visual hook"]
        shots_per = 1
    elif category == "Trailer":
        target = max(base, 30.0)
        rhythm = "tease → escalate → smash title"
        notes = ["Trailer smash-cut rhythm", "Short aggressive shot lengths"]
        shots_per = 2
    elif category in ("Advertisement", "Product Video"):
        target = max(15.0, min(base, 45.0))
        rhythm = "hook → benefit → brand resolve"
        notes = ["Commercial clarity", "Product readable within first third"]
        shots_per = 2
    elif category == "Podcast":
        target = max(base, 20.0)
        rhythm = "host intro → talk beat → close"
        notes = ["Talk-led pacing", "Minimal cutaways"]
        shots_per = 1
    else:
        # Narrative / music / documentary / islamic / short film
        target = max(base, float(max(18, beat_count * 3)))
        rhythm = "establish → deepen → turn → resolve"
        notes = ["Narrative cinematic pacing", "Hold emotional beats"]
        shots_per = 2 if beat_count <= 4 else 1

    # Prefer natural beat count when story cues demand more scenes.
    scene_count = max(2, beat_count)
    if target <= 12:
        scene_count = min(scene_count, 3)
    elif target >= 45 and scene_count < 5:
        scene_count = max(scene_count, 5)

    return PacingPlan(
        target_runtime=round(target, 1),
        scene_count=scene_count,
        shots_per_scene=shots_per,
        story_rhythm=rhythm,
        notes=notes,
    )


def distribute_durations(total: float, parts: int) -> list[float]:
    """Weighted cinematic distribution — slightly longer open/close."""
    if parts <= 0:
        return []
    if parts == 1:
        return [round(total, 2)]
    weights = []
    for i in range(parts):
        if i == 0 or i == parts - 1:
            weights.append(1.25)
        elif i == parts // 2:
            weights.append(1.15)
        else:
            weights.append(1.0)
    wsum = sum(weights)
    raw = [total * (w / wsum) for w in weights]
    # Fix rounding drift on last beat.
    rounded = [round(x, 2) for x in raw[:-1]]
    rounded.append(round(total - sum(rounded), 2))
    return rounded
