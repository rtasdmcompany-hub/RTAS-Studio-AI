"""Module 3 — Scene Planner."""

from __future__ import annotations

from app.services.intelligence.models import (
    PromptIntelligenceResult,
    ScenePlan,
)


def plan_scenes(
    prompt: str,
    intelligence: PromptIntelligenceResult,
) -> list[ScenePlan]:
    total = max(5, int(intelligence.estimated_duration_seconds or 15))
    # 2–4 scenes depending on duration.
    count = 2 if total <= 15 else 3 if total <= 45 else 4
    base = total // count
    remainder = total - base * count

    templates = [
        ("Opening establish", "Introduce world and subject", "environment reveal", "cut"),
        ("Core action", "Primary message / performance", "focused action", "match cut"),
        ("Emotional beat", "Deepen emotion and stakes", "character reaction", "dissolve"),
        ("Closing resolve", "Resolve and brand payoff", "hero hold", "fade"),
    ]

    scenes: list[ScenePlan] = []
    for i in range(count):
        title, desc_prefix, action, transition = templates[i]
        duration = base + (1 if i < remainder else 0)
        scenes.append(
            ScenePlan(
                index=i,
                title=title,
                duration_seconds=duration,
                description=f"{desc_prefix}. Source intent: {prompt[:180]}",
                environment=intelligence.lighting,
                characters=["lead subject"] if intelligence.style != "cartoon" else ["stylized lead"],
                actions=[action, intelligence.emotion],
                transitions=transition if i < count - 1 else "end card",
            )
        )
    return scenes
