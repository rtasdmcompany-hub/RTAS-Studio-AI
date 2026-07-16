"""Module 1 — Cinematic Reasoning Engine."""

from __future__ import annotations

from app.services.intelligence.cinematic_models import CinematicReasoning
from app.services.intelligence.models import PromptIntelligenceResult


def reason_about_project(
    prompt: str,
    intelligence: PromptIntelligenceResult,
) -> CinematicReasoning:
    text = (prompt or "").strip()
    genre = intelligence.cinematic_genre.replace("_", " ")
    emotion = intelligence.emotion
    style = intelligence.style

    audience = "general streaming audience"
    if intelligence.category == "business":
        audience = "brand / conversion audience"
    elif intelligence.category == "religious":
        audience = "faith-aware family audience"
    elif intelligence.category == "cartoon":
        audience = "family / youth audience"
    elif intelligence.category == "song":
        audience = "music / social audience"

    production_style = "premium digital cinema"
    if "luxury" in text.lower():
        production_style = "luxury brand film"
    elif intelligence.category == "podcast":
        production_style = "talk-led cinematic"

    themes: list[str] = [emotion, genre]
    if "success" in text.lower() or "launch" in text.lower():
        themes.append("ambition")
    if "family" in text.lower() or "love" in text.lower():
        themes.append("connection")

    logline = text[:160] + ("…" if len(text) > 160 else "")
    story = (
        f"A {genre} piece centered on {emotion} stakes, "
        f"told in a {style} visual register for {audience}."
    )
    arc = (
        "setup → tension → emotional turn → resolve"
        if intelligence.estimated_duration_seconds >= 20
        else "hook → payoff"
    )

    return CinematicReasoning(
        story=story,
        emotion=emotion,
        genre=genre,
        character_arc=arc,
        audience=audience,
        production_style=production_style,
        themes=themes,
        logline=logline,
    )
