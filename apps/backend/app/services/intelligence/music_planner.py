"""Module 4 — Music Planner (planning only, no audio generation)."""

from __future__ import annotations

from app.services.intelligence.cinematic_models import EmotionMap, MusicPlan
from app.services.intelligence.models import PromptIntelligenceResult, ScenePlan


def plan_music(
    intelligence: PromptIntelligenceResult,
    scenes: list[ScenePlan],
    emotion_map: EmotionMap,
) -> MusicPlan:
    genre = "cinematic orchestral"
    if intelligence.category == "song":
        genre = "contemporary pop/hip-hop bed"
    elif intelligence.category == "business":
        genre = "modern corporate hybrid"
    elif intelligence.emotion == "calm":
        genre = "ambient piano"

    tempo = 92
    energy = "medium"
    if intelligence.emotion in ("dramatic", "joyful"):
        tempo = 118
        energy = "high"
    elif intelligence.emotion == "calm":
        tempo = 72
        energy = "low"

    instrumentation = ["strings", "soft percussion", "pads"]
    if intelligence.category == "song":
        instrumentation = ["drums", "bass", "synth lead", "vocals bed"]
    elif intelligence.category == "religious":
        instrumentation = ["soft choir pads", "strings", "gentle percussion"]

    transitions = ["intro swell", "midrise hit", "outro resolve"]
    cues = []
    t = 0
    for scene in scenes:
        cues.append(
            {
                "scene_index": scene.index,
                "start_sec": t,
                "end_sec": t + scene.duration_seconds,
                "emotion": next(
                    (b.emotion for b in emotion_map.beats if b.scene_index == scene.index),
                    intelligence.emotion,
                ),
            }
        )
        t += scene.duration_seconds

    return MusicPlan(
        genre=genre,
        tempo_bpm=tempo,
        energy=energy,
        emotion=intelligence.emotion,
        instrumentation=instrumentation,
        beat_transitions=transitions,
        cue_timing=cues,
    )
