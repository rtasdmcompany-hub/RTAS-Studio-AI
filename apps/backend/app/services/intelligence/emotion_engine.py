"""Module 3 — Emotion Engine (scene-by-scene map)."""

from __future__ import annotations

from app.services.intelligence.cinematic_models import EmotionBeat, EmotionMap
from app.services.intelligence.models import PromptIntelligenceResult, ScenePlan

_SEQUENCE = ("setup", "hope", "tension", "turn", "victory", "resolve")


def build_emotion_map(
    scenes: list[ScenePlan],
    intelligence: PromptIntelligenceResult,
) -> EmotionMap:
    primary = intelligence.emotion
    beats: list[EmotionBeat] = []
    for i, scene in enumerate(scenes):
        label = _SEQUENCE[min(i, len(_SEQUENCE) - 1)]
        if i == 0:
            emotion = "setup"
            intensity = 0.4
        elif i == len(scenes) // 2:
            emotion = primary
            intensity = 0.85
        elif i == len(scenes) - 1:
            emotion = "victory" if primary in ("inspiring", "joyful") else "resolve"
            intensity = 0.7
        else:
            emotion = "suspense" if primary == "dramatic" else primary
            intensity = 0.65
        beats.append(
            EmotionBeat(
                scene_index=scene.index,
                emotion=emotion,
                intensity=intensity,
                notes=f"{scene.title}: {label} beat",
            )
        )

    arc = " → ".join(b.emotion for b in beats) if beats else primary
    return EmotionMap(primary_emotion=primary, beats=beats, arc=arc)
