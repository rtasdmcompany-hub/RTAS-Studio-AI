"""
Cinematic Prompt Understanding Engine.

Parses free-form user prompts into structured Hollywood-style production
instructions. Deterministic, modular, production-ready — no mock paths.
"""

from __future__ import annotations

from typing import Any

from app.services.intelligence.prompt_understanding.detectors import (
    detect_atmosphere,
    detect_camera,
    detect_category,
    detect_color_grading,
    detect_color_palette,
    detect_emotions,
    detect_environment,
    detect_lens,
    detect_lighting,
    detect_mood,
    detect_movement,
    detect_music,
    detect_subject_count,
    detect_time,
    detect_transition,
    detect_weather,
)
from app.services.intelligence.prompt_understanding.models import (
    CinematicPromptUnderstanding,
)


def understand_prompt(
    prompt: str,
    *,
    category_hint: str | None = None,
) -> CinematicPromptUnderstanding:
    raw = (prompt or "").strip()
    text = raw.lower()

    category = detect_category(text, category_hint=category_hint)
    time = detect_time(text)
    weather = detect_weather(text)
    emotions = detect_emotions(text)
    mood = detect_mood(text, emotions)
    movement = detect_movement(text)
    camera = detect_camera(text, emotions, movement)
    shot_types = [c for c in camera if any(
        token in c.lower()
        for token in ("close", "medium", "wide", "pov", "shoulder", "macro", "aerial")
    )]
    if not shot_types:
        shot_types = list(camera[:2])
    lens = detect_lens(text, shot_types)
    lighting = detect_lighting(text, time, weather, emotions)
    color_palette = detect_color_palette(text, time, weather, emotions, category)
    music_style = detect_music(text, emotions, category)
    environment = detect_environment(text, weather)
    subject_count = detect_subject_count(text)
    transition_style = detect_transition(category, mood)
    visual_atmosphere = detect_atmosphere(
        time, weather, mood, emotions, environment
    )
    color_grading = detect_color_grading(color_palette, time, weather)

    confidence = 0.5
    if len(raw) >= 24:
        confidence += 0.15
    if len(raw) >= 60:
        confidence += 0.1
    if weather != "Clear" or time != "Day":
        confidence += 0.1
    if len(emotions) > 1:
        confidence += 0.05
    if category_hint:
        confidence += 0.05
    confidence = min(0.97, round(confidence, 2))

    return CinematicPromptUnderstanding(
        scene_type=category,
        camera=camera,
        lighting=lighting,
        lens=lens,
        movement=movement,
        environment=environment,
        mood=mood,
        emotion=emotions,
        weather=weather,
        time=time,
        color_palette=color_palette,
        music_style=music_style,
        transition_style=transition_style,
        shot_types=shot_types,
        visual_atmosphere=visual_atmosphere,
        subject_count=subject_count,
        category=category,
        color_grading=color_grading,
        confidence=confidence,
        raw_prompt=raw,
    )


def understand_prompt_dict(prompt: str, **kwargs: Any) -> dict[str, Any]:
    result = understand_prompt(prompt, **kwargs)
    return result.production_instructions()
