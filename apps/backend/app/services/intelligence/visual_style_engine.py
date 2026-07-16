"""Module 2 — Visual Style Engine."""

from __future__ import annotations

from app.services.intelligence.cinematic_models import VisualStylePlan
from app.services.intelligence.models import PromptIntelligenceResult

_LOOKS = (
    ("imax", "IMAX"),
    ("netflix", "Netflix"),
    ("apple", "Apple TV+"),
    ("hollywood", "Anime"),
    ("documentary", "Documentary"),
    ("music video", "Music Video"),
    ("luxury", "Luxury Brand"),
    ("commercial", "Commercial"),
    ("hollywood", "Anime"),
)


def plan_visual_style(
    prompt: str,
    intelligence: PromptIntelligenceResult,
) -> VisualStylePlan:
    lower = (prompt or "").lower()
    reference = "Hollywood"
    for key, label in _LOOKS:
        if key in lower:
            reference = label
            break
    else:
        if intelligence.category == "business":
            reference = "Commercial"
        elif intelligence.category == "song":
            reference = "Music Video"
        elif intelligence.category == "cartoon":
            reference = "Anime"
        elif intelligence.cinematic_genre == "documentary":
            reference = "Documentary"

    palettes = {
        "inspiring": ["warm gold", "clean white", "deep teal"],
        "dramatic": ["charcoal", "crimson accent", "cold blue"],
        "calm": ["soft sage", "mist grey", "pale amber"],
        "joyful": ["sunlit yellow", "coral", "sky blue"],
        "somber": ["desaturated blue", "slate", "muted amber"],
    }
    palette = palettes.get(intelligence.emotion, ["neutral cinema", "soft contrast"])

    lighting = intelligence.lighting
    if reference == "Luxury Brand":
        lighting = "soft key + specular highlights"
    elif reference == "IMAX":
        lighting = "large-format natural + volumetric"
    elif reference == "Music Video":
        lighting = "stylized practicals + rhythmic accents"

    contrast = "high" if intelligence.emotion in ("dramatic", "somber") else "balanced"
    mood = f"{intelligence.emotion} {reference.lower()} mood"
    film_stock = "digital cinema clean" if reference != "Documentary" else "observational grain"
    lens = "anamorphic flare language" if reference in ("Hollywood", "IMAX") else "spherical primes"
    camera_language = (
        "motivated push-ins and locked hero frames"
        if reference in ("Commercial", "Luxury Brand")
        else "dynamic coverage with editorial rhythm"
    )

    return VisualStylePlan(
        lighting=lighting,
        color_palette=palette,
        mood=mood,
        contrast=contrast,
        film_stock_style=film_stock,
        lens_style=lens,
        camera_language=camera_language,
        reference_look=reference,
    )
