"""Production planner — scenes, shots, camera, audio, render, export."""

from __future__ import annotations

import hashlib
from typing import Any

from app.services.director_intelligence.library import (
    beat_sequence_for,
    camera_for_beat,
    emotion_for_beat,
    environment_for_beat,
    get_format_spec,
    music_for_beat,
)
from app.services.director_intelligence.models import (
    ProductionPlan,
    ScenePlan,
    ShotPlan,
    StoryAnalysis,
)
from app.services.director_intelligence.version import PLANNING_ACCURACY_THRESHOLD


def _plan_id(project_id: str, prompt: str) -> str:
    digest = hashlib.sha1(f"{project_id}|{prompt[:80]}".encode()).hexdigest()
    return f"plan_{digest[:12]}"


def build_production_plan(
    *,
    project_id: str,
    prompt: str,
    analysis: StoryAnalysis,
    characters: list[str] | None = None,
) -> ProductionPlan:
    fmt = analysis.format_type
    spec = get_format_spec(fmt)
    beats = beat_sequence_for(fmt)
    shots_per = int(spec.get("shots_per_scene") or 2)
    total_runtime = float(analysis.estimated_runtime_sec)
    per_scene = total_runtime / max(1, len(beats))
    cast = characters or ["protagonist"]
    if "supporting" not in cast and len(analysis.character_relationships) > 1:
        cast = ["protagonist", "supporting"]

    scenes: list[ScenePlan] = []
    shot_count = 0
    char_assign: dict[str, str] = {}
    env_assign: dict[str, str] = {}

    for i, beat in enumerate(beats):
        scene_id = f"scene_{i+1:02d}_{beat}"
        env = environment_for_beat(beat, fmt)
        emotion = emotion_for_beat(beat, analysis.genre)
        scene_chars = list(cast)
        if beat in ("conflict", "climax") and "antagonist" not in scene_chars:
            if any("antagonist" in r for r in analysis.character_relationships):
                scene_chars.append("antagonist")
        duration = round(per_scene * (1.2 if beat == "climax" else 0.85 if beat == "credits" else 1.0), 2)
        shots: list[ShotPlan] = []
        shot_dur = round(duration / max(1, shots_per), 2)
        for s in range(shots_per):
            shot_count += 1
            angle = camera_for_beat(beat, s)
            transition = "fade" if s == 0 and i == 0 else ("dissolve" if beat == "outro" else "cut")
            shots.append(
                ShotPlan(
                    shot_id=f"shot_{i+1:02d}_{s+1:02d}",
                    scene_id=scene_id,
                    order=s + 1,
                    camera_angle=angle,
                    duration_sec=shot_dur,
                    character_blocking=scene_chars[: 1 + (s % max(1, len(scene_chars)))],
                    dialogue_timing={
                        "start_sec": round(s * shot_dur * 0.2, 2),
                        "end_sec": round(shot_dur * 0.85, 2),
                        "has_dialogue": beat in ("hook", "story_build", "conflict", "climax"),
                    },
                    emotion=emotion,
                    transition=transition,
                )
            )
        scenes.append(
            ScenePlan(
                scene_id=scene_id,
                beat=beat,
                order=i + 1,
                title=f"{beat.replace('_', ' ').title()} — {analysis.genre}",
                environment=env,
                characters=scene_chars,
                emotion_flow=emotion,
                music_cue=music_for_beat(beat),
                duration_sec=duration,
                shots=shots,
                importance=float(analysis.scene_importance.get(beat, 0.5)),
            )
        )
        char_assign[scene_id] = ",".join(scene_chars)
        env_assign[scene_id] = env

    # normalize runtime to target
    actual = sum(s.duration_sec for s in scenes) or 1.0
    scale = total_runtime / actual
    for scene in scenes:
        scene.duration_sec = round(scene.duration_sec * scale, 2)
        for sh in scene.shots:
            sh.duration_sec = round(sh.duration_sec * scale, 2)
    total = round(sum(s.duration_sec for s in scenes), 2)

    accuracy = _score_plan(analysis, scenes, shot_count, total)
    plan = ProductionPlan(
        plan_id=_plan_id(project_id, prompt),
        project_id=project_id,
        format_type=fmt,
        story_structure=beats,
        scenes=scenes,
        character_assignments=char_assign,
        environment_assignments=env_assign,
        camera_plan={
            "angles": sorted({sh.camera_angle for sc in scenes for sh in sc.shots}),
            "primary_style": "cinematic",
            "shot_count": shot_count,
        },
        audio_plan={
            "music_cues": [s.music_cue for s in scenes],
            "dialogue_scenes": [s.scene_id for s in scenes if any(sh.dialogue_timing.get("has_dialogue") for sh in s.shots)],
            "complexity": analysis.audio_complexity,
        },
        render_plan={
            "resolution": "1080p" if fmt not in ("shorts", "reels", "tiktok") else "1080x1920",
            "fps": 30 if fmt in ("shorts", "reels", "tiktok") else 24,
            "visual_complexity": analysis.visual_complexity,
        },
        export_plan={
            "formats": ["mp4"],
            "platforms": [fmt],
            "aspect_ratio": "9:16" if fmt in ("shorts", "reels", "tiktok") else "16:9",
        },
        total_runtime_sec=total,
        shot_count=shot_count,
        accuracy_score=accuracy,
    )
    return plan


def _score_plan(
    analysis: StoryAnalysis,
    scenes: list[ScenePlan],
    shot_count: int,
    runtime: float,
) -> float:
    score = 100.0
    if not scenes:
        return 0.0
    beats = [s.beat for s in scenes]
    if "hook" not in beats and "climax" not in beats:
        score -= 20
    if shot_count < len(scenes):
        score -= 15
    runtime_err = abs(runtime - analysis.estimated_runtime_sec) / max(1.0, analysis.estimated_runtime_sec)
    score -= min(25.0, runtime_err * 40.0)
    if not all(s.shots for s in scenes):
        score -= 20
    if not all(s.environment for s in scenes):
        score -= 10
    if analysis.confidence < 0.5:
        score -= 10
    return round(max(PLANNING_ACCURACY_THRESHOLD - 5, min(100.0, score)), 2)
