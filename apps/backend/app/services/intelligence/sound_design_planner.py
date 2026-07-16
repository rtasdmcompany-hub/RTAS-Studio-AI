"""Module 6 — Sound Design Planner (planning only)."""

from __future__ import annotations

from app.services.intelligence.cinematic_models import SoundDesignPlan, VisualStylePlan
from app.services.intelligence.models import PromptIntelligenceResult


def plan_sound_design(
    prompt: str,
    intelligence: PromptIntelligenceResult,
    visual: VisualStylePlan,
) -> SoundDesignPlan:
    lower = (prompt or "").lower()
    ambient = ["room tone"]
    if "city" in lower or "street" in lower:
        ambient.append("distant traffic bed")
    if "office" in lower:
        ambient.append("soft office hum")
    if visual.reference_look == "Music Video":
        ambient.append("club air / venue bed")

    foley = ["footsteps", "cloth movement"]
    if "phone" in lower:
        foley.append("phone tap")
    if "door" in lower:
        foley.append("door latch")

    transitions = ["whoosh soft", "impact low", "silence beat"]
    env_fx = ["air movement"]
    if "rain" in lower:
        env_fx.append("rain loop")
    if "night" in lower:
        env_fx.append("night insects / distant city")

    layers = ["music bed ducking under VO", "subtle risers on scene turns"]
    if intelligence.category == "business":
        layers.append("UI/product interaction ticks (subtle)")

    return SoundDesignPlan(
        ambient=ambient,
        foley=foley,
        transitions=transitions,
        environmental_fx=env_fx,
        background_layers=layers,
    )
