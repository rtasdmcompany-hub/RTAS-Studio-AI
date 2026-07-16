"""Module 4 — Story Continuity Engine."""

from __future__ import annotations

import re

from app.services.intelligence.director_models import (
    CharacterMemory,
    ContinuityState,
)
from app.services.intelligence.models import PromptIntelligenceResult, ScenePlan


def build_continuity_state(
    prompt: str,
    intelligence: PromptIntelligenceResult,
    scenes: list[ScenePlan],
    characters: list[CharacterMemory],
) -> ContinuityState:
    lower = (prompt or "").lower()

    time_of_day = "day"
    if "night" in lower or "moon" in lower:
        time_of_day = "night"
    elif "sunset" in lower or "golden hour" in lower:
        time_of_day = "golden hour"
    elif "morning" in lower:
        time_of_day = "morning"

    weather = "clear"
    if "rain" in lower:
        weather = "rain"
    elif "fog" in lower or "mist" in lower:
        weather = "fog"
    elif "snow" in lower:
        weather = "snow"

    location = "primary location"
    for key in ("office", "street", "studio", "home", "mosque", "stage", "city"):
        if key in lower:
            location = key
            break

    positions = {
        c.character_id: "frame-center" if i == 0 else "supporting-left"
        for i, c in enumerate(characters)
    }
    wardrobe = {c.character_id: c.outfit for c in characters}

    objects: list[str] = []
    for token in ("phone", "laptop", "watch", "car", "mic", "book"):
        if token in lower:
            objects.append(token)

    emotion_arc = [intelligence.emotion for _ in scenes]
    if len(emotion_arc) >= 3:
        emotion_arc[0] = "setup"
        emotion_arc[len(emotion_arc) // 2] = intelligence.emotion
        emotion_arc[-1] = "resolve"

    contradictions: list[str] = []
    # Detect impossible day/night flips inside prompt fragments.
    if "night" in lower and "midday sun" in lower:
        contradictions.append("time_of_day_conflict")
    # Wardrobe must stay constant unless prompt explicitly changes clothes.
    if not re.search(r"\b(change(s|d)? outfit|wardrobe change|new clothes)\b", lower):
        for scene in scenes:
            if "different outfit" in scene.description.lower():
                contradictions.append(
                    f"scene_{scene.index}_wardrobe_drift_blocked"
                )

    return ContinuityState(
        character_positions=positions,
        time_of_day=time_of_day,
        weather=weather,
        location=location,
        wardrobe=wardrobe,
        objects=objects,
        emotion_arc=emotion_arc,
        contradictions=contradictions,
    )
