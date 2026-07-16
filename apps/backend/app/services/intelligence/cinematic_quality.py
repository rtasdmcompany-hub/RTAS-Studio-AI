"""Module 7 — Cinematic Quality Score."""

from __future__ import annotations

from typing import Any

from app.services.intelligence.cinematic_models import CinematicQualityScore


def score_cinematic_quality(
    *,
    prompt: str,
    enhanced_prompt: str,
    scenes: list[Any],
    shots: list[Any],
    cameras: list[Any],
    character_memory: list[dict[str, Any]],
    continuity: dict[str, Any],
    visual_style: dict[str, Any],
    emotion_map: dict[str, Any],
) -> CinematicQualityScore:
    notes: list[str] = []

    prompt_quality = 0.45
    if len((prompt or "").strip()) >= 40:
        prompt_quality += 0.25
    if len((enhanced_prompt or "").strip()) > len((prompt or "").strip()):
        prompt_quality += 0.2
    prompt_quality = min(1.0, prompt_quality)

    story = 0.5 + (0.1 * min(4, len(scenes)))
    story = min(1.0, story)
    if not scenes:
        story = 0.2
        notes.append("missing_scenes")

    camera = 0.55
    if cameras:
        camera += 0.25
    if shots and len(shots) >= len(scenes):
        camera += 0.15
    camera = min(1.0, camera)

    emotion = 0.5
    beats = (emotion_map or {}).get("beats") or []
    if beats:
        emotion += 0.3
    if (emotion_map or {}).get("arc"):
        emotion += 0.15
    emotion = min(1.0, emotion)

    character_consistency = 0.4
    if character_memory:
        character_consistency += 0.4
        if all(c.get("locked_traits") for c in character_memory):
            character_consistency += 0.15
    character_consistency = min(1.0, character_consistency)

    scene_continuity = 0.5
    if continuity and not continuity.get("contradictions"):
        scene_continuity += 0.35
    elif continuity.get("contradictions"):
        scene_continuity -= 0.2
        notes.append("continuity_contradictions")
    scene_continuity = max(0.0, min(1.0, scene_continuity))

    lighting = 0.55
    if (visual_style or {}).get("lighting"):
        lighting += 0.25
    if (visual_style or {}).get("color_palette"):
        lighting += 0.15
    lighting = min(1.0, lighting)

    visual_quality = 0.5
    if (visual_style or {}).get("reference_look"):
        visual_quality += 0.25
    if (visual_style or {}).get("camera_language"):
        visual_quality += 0.15
    visual_quality = min(1.0, visual_quality)

    overall = round(
        (
            story
            + camera
            + emotion
            + prompt_quality
            + character_consistency
            + scene_continuity
            + lighting
            + visual_quality
        )
        / 8.0,
        3,
    )

    return CinematicQualityScore(
        story=round(story, 3),
        camera=round(camera, 3),
        emotion=round(emotion, 3),
        prompt_quality=round(prompt_quality, 3),
        character_consistency=round(character_consistency, 3),
        scene_continuity=round(scene_continuity, 3),
        lighting=round(lighting, 3),
        visual_quality=round(visual_quality, 3),
        overall=overall,
        notes=notes,
    )
