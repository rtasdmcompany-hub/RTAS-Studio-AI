"""
Production Render & Export Engine.

Combines scenes, shots, audio, captions, transitions, effects, and metadata
into one final production package with validated export specs.
"""

from __future__ import annotations

from typing import Any

from app.services.intelligence.models import (
    CameraPlan,
    ExportPlan,
    PromptIntelligenceResult,
    ScenePlan,
    ShotPlan,
)
from app.services.intelligence.production_render.assets import build_asset_inventory
from app.services.intelligence.production_render.captions import (
    build_captions,
    render_srt,
)
from app.services.intelligence.production_render.export_specs import (
    build_export_specs,
    primary_export_spec,
)
from app.services.intelligence.production_render.models import (
    ProductionRenderPackage,
    ThumbnailInstruction,
    VideoManifest,
)
from app.services.intelligence.production_render.validator import validate_export_package


def _scene_dicts(scenes: list[ScenePlan] | list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for s in scenes:
        out.append(s.to_dict() if hasattr(s, "to_dict") else dict(s))
    return out


def _shot_dicts(shots: list[ShotPlan] | list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for s in shots:
        out.append(s.to_dict() if hasattr(s, "to_dict") else dict(s))
    return out


def _build_transitions(
    scenes: list[dict[str, Any]],
    director_plan: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    style = (director_plan or {}).get("transition_style") or "motivated cut"
    transitions = []
    t = 0.0
    for i, scene in enumerate(scenes):
        dur = float(scene.get("duration_seconds") or 1)
        t += dur
        if i < len(scenes) - 1:
            transitions.append(
                {
                    "at_sec": round(t, 2),
                    "from_scene": scene.get("index", i),
                    "to_scene": scenes[i + 1].get("index", i + 1),
                    "type": scene.get("transitions") or style,
                }
            )
    return transitions


def _build_effects(
    understanding: dict[str, Any] | None,
    visual_style: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    effects = [
        {"kind": "color_grade", "value": (visual_style or {}).get("color_palette") or ["cinematic"]},
        {"kind": "lighting_look", "value": (visual_style or {}).get("lighting") or "natural"},
    ]
    if understanding:
        effects.append(
            {
                "kind": "atmosphere",
                "value": understanding.get("visual_atmosphere")
                or understanding.get("mood"),
            }
        )
        if str(understanding.get("weather") or "").lower() == "rain":
            effects.append({"kind": "weather_overlay", "value": "rain_streaks_subtle"})
    return effects


def _thumbnails(
    scenes: list[dict[str, Any]],
    character_memory: list[dict[str, Any]],
    understanding: dict[str, Any] | None,
) -> list[ThumbnailInstruction]:
    subject = "lead subject"
    if character_memory:
        subject = str(character_memory[0].get("character_id") or subject)
    mood = str((understanding or {}).get("mood") or "Cinematic")
    thumbs: list[ThumbnailInstruction] = []
    t = 0.0
    for i, scene in enumerate(scenes[:3]):
        dur = float(scene.get("duration_seconds") or 3)
        ts = t + max(0.4, dur * 0.35)
        thumbs.append(
            ThumbnailInstruction(
                timestamp_sec=round(ts, 2),
                framing="close-up" if "close" in str(scene.get("title") or "").lower() else "medium",
                subject=subject,
                mood=mood,
                text_safe_area="lower-third clear",
                notes=[
                    f"From scene: {scene.get('title')}",
                    "High contrast poster frame; face readable",
                ],
            )
        )
        t += dur
    if not thumbs:
        thumbs.append(
            ThumbnailInstruction(
                timestamp_sec=1.0,
                framing="medium",
                subject=subject,
                mood=mood,
                text_safe_area="center-safe",
                notes=["Fallback hero frame"],
            )
        )
    return thumbs


def build_production_render(
    *,
    prompt: str,
    enhanced_prompt: str,
    intelligence: PromptIntelligenceResult,
    scenes: list[ScenePlan] | list[dict[str, Any]],
    shots: list[ShotPlan] | list[dict[str, Any]],
    cameras: list[CameraPlan] | list[dict[str, Any]],
    character_memory: list[dict[str, Any]],
    director_plan: dict[str, Any],
    timeline: dict[str, Any],
    understanding: dict[str, Any] | None = None,
    audio_director: dict[str, Any] | None = None,
    music_plan: dict[str, Any] | None = None,
    voice_plan: dict[str, Any] | None = None,
    sound_plan: dict[str, Any] | None = None,
    visual_style: dict[str, Any] | None = None,
    scene_breakdown: dict[str, Any] | None = None,
    character_consistency: dict[str, Any] | None = None,
    continuity: dict[str, Any] | None = None,
    quality_report: dict[str, Any] | None = None,
    export_seed: ExportPlan | None = None,
) -> ProductionRenderPackage:
    scene_dicts = _scene_dicts(scenes)
    shot_dicts = _shot_dicts(shots)
    camera_dicts = [
        c.to_dict() if hasattr(c, "to_dict") else dict(c) for c in cameras
    ]

    runtime = float(
        timeline.get("total_duration_seconds")
        or sum(float(s.get("duration_seconds") or 0) for s in scene_dicts)
        or intelligence.estimated_duration_seconds
        or 15
    )

    export_specs = build_export_specs(intelligence, understanding=understanding)
    primary = primary_export_spec(export_specs)
    captions = build_captions(
        scenes=scene_dicts,
        audio_director=audio_director,
        prompt=prompt,
    )
    subtitle_file = render_srt(captions)
    assets = build_asset_inventory(
        scenes=scene_dicts,
        shots=shot_dicts,
        character_memory=character_memory,
        audio_director=audio_director,
        understanding=understanding,
    )
    transitions = _build_transitions(scene_dicts, director_plan)
    effects = _build_effects(understanding, visual_style)
    thumbs = _thumbnails(scene_dicts, character_memory, understanding)

    voice_package = {
        "plan": voice_plan or {},
        "timeline": (audio_director or {}).get("voice_timeline") or [],
        "lip_sync_timeline": (audio_director or {}).get("lip_sync_timeline") or [],
        "narration_notes": (audio_director or {}).get("narration_notes") or [],
        "silence_windows": (audio_director or {}).get("silence_windows") or [],
    }
    music_package = {
        "plan": music_plan or {},
        "timeline": (audio_director or {}).get("music_timeline") or [],
        "sfx_timeline": (audio_director or {}).get("sfx_timeline") or [],
        "sound_plan": sound_plan or {},
        "mix_notes": (audio_director or {}).get("mix_notes") or [],
    }

    director_notes = list(director_plan.get("director_notes") or [])
    director_notes.append(
        f"Deliver primary export {primary.format.upper()} {primary.aspect} {primary.resolution}"
    )

    video_manifest = VideoManifest(
        version="1.0",
        title=(prompt or "RTAS Production")[:80],
        runtime_seconds=round(runtime, 2),
        scenes=len(scene_dicts),
        shots=len(shot_dicts),
        tracks={
            "video": {"shots": len(shot_dicts), "transitions": len(transitions)},
            "audio_voice": {"cues": len(voice_package["timeline"])},
            "audio_music": {"cues": len(music_package["timeline"])},
            "audio_sfx": {"cues": len(music_package["sfx_timeline"])},
            "captions": {"cues": len(captions), "format": "srt"},
        },
        export=primary.to_dict(),
        metadata={
            "category": (understanding or {}).get("category") or intelligence.category,
            "hdr": primary.hdr,
            "seed_export": export_seed.to_dict() if export_seed else {},
        },
    )

    json_package = {
        "prompt": prompt,
        "enhanced_prompt": enhanced_prompt,
        "prompt_understanding": understanding or {},
        "scenes": scene_dicts,
        "shots": shot_dicts,
        "camera_plan": camera_dicts,
        "character_memory": character_memory,
        "character_consistency": character_consistency or {},
        "scene_breakdown": scene_breakdown or {},
        "audio_director": audio_director or {},
        "voice_package": voice_package,
        "music_package": music_package,
        "timeline": timeline,
        "transitions": transitions,
        "effects": effects,
        "continuity": continuity or {},
        "director_plan": director_plan,
        "director_notes": director_notes,
        "visual_style": visual_style or {},
        "quality_report": quality_report or {},
        "captions": [c.to_dict() for c in captions],
        "export_specs": [e.to_dict() for e in export_specs],
        "video_manifest": video_manifest.to_dict(),
    }

    validation = validate_export_package(
        scenes=scene_dicts,
        shots=shot_dicts,
        timeline=timeline,
        captions=captions,
        subtitle_file=subtitle_file,
        export_specs=export_specs,
        video_manifest=video_manifest,
        voice_package=voice_package,
        music_package=music_package,
        camera_plan=camera_dicts,
        director_notes=director_notes,
    )

    return ProductionRenderPackage(
        json_package=json_package,
        timeline=timeline,
        assets=assets,
        video_manifest=video_manifest,
        subtitle_file=subtitle_file,
        captions=captions,
        thumbnail_instructions=thumbs,
        voice_package=voice_package,
        music_package=music_package,
        camera_plan=camera_dicts,
        director_notes=director_notes,
        effects=effects,
        transitions=transitions,
        export_specs=export_specs,
        validation=validation,
        metadata={
            "engine": "production_render",
            "version": "1.0",
            "primary_export": primary.to_dict(),
        },
    )


def build_production_render_dict(**kwargs: Any) -> dict[str, Any]:
    return build_production_render(**kwargs).to_dict()


def to_export_plan(package: ProductionRenderPackage) -> ExportPlan:
    primary = primary_export_spec(package.export_specs)
    notes = [
        f"Aspect={primary.aspect}",
        f"HDR={'yes' if primary.hdr else 'no'}",
        f"Validation={'pass' if package.validation.passed else 'fail'} ({package.validation.score})",
        f"Subtitles={len(package.captions)} cues",
        *primary.notes[:2],
    ]
    return ExportPlan(
        format=primary.format,
        resolution=primary.resolution if primary.resolution != "8k_ready" else "4k",
        container=primary.codec_video,
        audio_mix=f"{primary.audio_channels}_normalized",
        delivery_notes=notes,
    )
