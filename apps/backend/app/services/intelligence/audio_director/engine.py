"""
AI Audio Director Engine.

Plans voice, music, SFX, silence, and lip-sync timelines before generation.
No audio synthesis — production planning only.
"""

from __future__ import annotations

from typing import Any

from app.services.intelligence.audio_director.detectors import run_audio_detection
from app.services.intelligence.audio_director.lip_sync import build_lip_sync_timeline
from app.services.intelligence.audio_director.models import AudioDirectorPlan
from app.services.intelligence.audio_director.timelines import (
    build_music_timeline,
    build_sfx_timeline,
    build_silence_windows,
    build_voice_timeline,
)
from app.services.intelligence.models import PromptIntelligenceResult, ScenePlan


def build_audio_director_plan(
    prompt: str,
    *,
    intelligence: PromptIntelligenceResult,
    scenes: list[ScenePlan],
    understanding: dict[str, Any] | None = None,
    character_memory: list[dict[str, Any]] | None = None,
    sound_plan: dict[str, Any] | None = None,
    director_plan: dict[str, Any] | None = None,
) -> AudioDirectorPlan:
    detection = run_audio_detection(
        prompt,
        intelligence,
        understanding=understanding,
        character_memory=character_memory,
    )
    lead_id = None
    if character_memory:
        lead_id = str(character_memory[0].get("character_id") or "Character_A")
    else:
        lead_id = "Character_A"

    voice_tl = build_voice_timeline(detection, scenes, character_id=lead_id)
    music_tl = build_music_timeline(detection, scenes)
    sfx_tl = build_sfx_timeline(
        detection,
        scenes,
        understanding=understanding,
        sound_plan=sound_plan,
    )
    lip_tl = build_lip_sync_timeline(
        detection,
        voice_tl,
        prompt=prompt,
        character_id=lead_id,
        scenes=scenes,
    )

    runtime = float(sum(max(1, s.duration_seconds) for s in scenes)) if scenes else float(
        intelligence.estimated_duration_seconds or 15
    )
    silence = build_silence_windows(detection, voice_tl, runtime)

    narration_notes = []
    dialogue_notes = []
    if detection.has_narration:
        narration_notes = [
            f"{detection.gender} {detection.speech_speed} narration",
            f"language={detection.language} accent={detection.accent}",
            f"emotion={detection.emotion}",
            *detection.pause_timing[:2],
        ]
    if detection.has_dialogue or detection.category == "podcast":
        dialogue_notes = [
            "Alternate speaker turns with clear lip-sync windows",
            f"Match character voice to Character Memory ({lead_id})",
        ]
    if detection.has_singing:
        dialogue_notes.append("Performance lip-sync on chorus / hook close-ups")

    mix_notes = [
        f"Voice={detection.volume_balance.get('voice', 0):.2f}",
        f"Music={detection.volume_balance.get('music', 0):.2f}",
        f"SFX={detection.volume_balance.get('sfx', 0):.2f}",
        f"Ambient={detection.volume_balance.get('ambient', 0):.2f}",
        "Duck music under VO by ~6–8 dB (planning guide)",
    ]
    if director_plan and director_plan.get("cinematic_rhythm"):
        mix_notes.append(f"Follow director rhythm: {director_plan['cinematic_rhythm']}")

    return AudioDirectorPlan(
        detection=detection,
        voice_timeline=voice_tl,
        music_timeline=music_tl,
        sfx_timeline=sfx_tl,
        lip_sync_timeline=lip_tl,
        narration_notes=narration_notes,
        dialogue_notes=dialogue_notes,
        silence_windows=silence,
        mix_notes=mix_notes,
        estimated_runtime_seconds=round(runtime, 2),
    )


def build_audio_director_plan_dict(prompt: str, **kwargs: Any) -> dict[str, Any]:
    return build_audio_director_plan(prompt, **kwargs).to_dict()
