"""
Scene Breakdown & Shot Generation Engine.

Converts one user prompt into a complete cinematic Production plan:
Scenes[], Shots[], Timeline, Estimated Runtime.
"""

from __future__ import annotations

from typing import Any

from app.services.intelligence.models import PromptIntelligenceResult
from app.services.intelligence.prompt_understanding.models import (
    CinematicPromptUnderstanding,
)
from app.services.intelligence.scene_breakdown.beats import detect_story_beats
from app.services.intelligence.scene_breakdown.models import (
    DetailedScene,
    ProductionBreakdown,
    TimelineBeat,
)
from app.services.intelligence.scene_breakdown.pacing import (
    distribute_durations,
    plan_pacing,
)
from app.services.intelligence.scene_breakdown.shot_engine import generate_shots_for_scene


def _transition_for_index(
    index: int,
    total: int,
    understanding: CinematicPromptUnderstanding,
    *,
    is_flashback: bool,
) -> str:
    if index >= total - 1:
        return "fade to hold"
    if is_flashback:
        return "dream dissolve"
    if understanding.mood == "Emotional":
        return "soft dissolve"
    return understanding.transition_style.split("+")[0].strip() or "cut"


def build_production_breakdown(
    prompt: str,
    *,
    understanding: CinematicPromptUnderstanding,
    intelligence: PromptIntelligenceResult,
    character_name: str = "lead subject",
) -> ProductionBreakdown:
    beats = detect_story_beats(prompt, understanding)
    pacing = plan_pacing(
        understanding=understanding,
        intelligence=intelligence,
        beat_count=len(beats),
    )

    # Align beat list to pacing scene_count (trim middle if needed, keep open/close).
    if len(beats) > pacing.scene_count and pacing.scene_count >= 2:
        keep = [beats[0]]
        middle = beats[1:-1]
        slots = pacing.scene_count - 2
        if slots > 0:
            step = max(1, len(middle) // slots) if middle else 1
            keep.extend(middle[::step][:slots])
        keep.append(beats[-1])
        beats = keep
    elif len(beats) < pacing.scene_count:
        # pacing wanted more — keep detected story beats (truth over padding)
        pass

    durations = distribute_durations(pacing.target_runtime, len(beats))
    scenes: list[DetailedScene] = []
    all_shots = []
    timeline: list[TimelineBeat] = []
    cursor = 0.0

    for i, (beat, dur) in enumerate(zip(beats, durations)):
        scene_number = i + 1
        transition = _transition_for_index(
            i,
            len(beats),
            understanding,
            is_flashback=beat.is_flashback,
        )
        shots = generate_shots_for_scene(
            scene_number=scene_number,
            beat=beat,
            understanding=understanding,
            scene_duration=dur,
            shots_per_scene=pacing.shots_per_scene,
            transition_type=transition,
            character_name=character_name,
        )
        scene = DetailedScene(
            scene_number=scene_number,
            scene_purpose=beat.purpose,
            title=beat.title,
            estimated_duration_seconds=dur,
            environment=shots[0].environment if shots else understanding.environment,
            weather=shots[0].weather if shots else understanding.weather,
            time=shots[0].time if shots else understanding.time,
            character_emotion=shots[0].character_emotion if shots else "Calm",
            lighting=shots[0].lighting if shots else list(understanding.lighting),
            color_palette=shots[0].color_palette if shots else list(understanding.color_palette),
            music_mood=shots[0].music_mood if shots else "Ambient",
            transition_type=transition,
            shots=shots,
        )
        scenes.append(scene)
        for shot in shots:
            all_shots.append(shot)
            start = cursor
            end = round(cursor + shot.estimated_duration_seconds, 2)
            timeline.append(
                TimelineBeat(
                    scene_number=scene_number,
                    shot_number=shot.shot_number,
                    start_seconds=round(start, 2),
                    end_seconds=end,
                    label=f"S{scene_number} Sh{shot.shot_number} — {shot.shot_type}",
                )
            )
            cursor = end

    runtime = round(cursor, 2)
    minutes = int(runtime // 60)
    seconds = int(round(runtime % 60))
    length = f"{minutes}m {seconds:02d}s" if minutes else f"{seconds}s"

    return ProductionBreakdown(
        prompt=(prompt or "").strip(),
        scenes=scenes,
        shots=all_shots,
        timeline=timeline,
        estimated_runtime_seconds=runtime,
        expected_video_length=length,
        pacing_notes=list(pacing.notes),
        story_rhythm=pacing.story_rhythm,
    )


def build_production_breakdown_dict(prompt: str, **kwargs: Any) -> dict[str, Any]:
    return build_production_breakdown(prompt, **kwargs).to_dict()
