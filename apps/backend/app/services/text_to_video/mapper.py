"""Convert Production Package JSON into scene/shot metadata + provider requests."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.services.text_to_video.models import (
    ProviderGenerationRequest,
    SceneMetadata,
    ShotMetadata,
    TextToVideoJob,
)
from app.services.text_to_video.prompts import (
    build_negative_prompt,
    build_shot_prompt,
    identity_lock_from_memory,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _job_id(parent: str | None, prompt: str) -> str:
    seed = f"{parent or ''}|{prompt}|{uuid4().hex[:8]}"
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:10]
    return f"t2v_{digest}"


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _extract_scenes_shots(
    production_package: dict[str, Any] | None,
    scene_breakdown: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    """Prefer detailed scene_breakdown; fall back to package plans."""
    pkg = production_package or {}
    breakdown = scene_breakdown or pkg.get("scene_breakdown") or {}
    production = breakdown.get("Production") if isinstance(breakdown, dict) else None
    if isinstance(production, dict) and production.get("Scenes"):
        scenes = _as_list(production.get("Scenes"))
        shots = _as_list(production.get("Shots"))
        prompt = str(production.get("prompt") or pkg.get("prompt") or "")
        return scenes, shots, prompt

    scenes = _as_list(pkg.get("scene_plan") or pkg.get("scenes"))
    shots = _as_list(pkg.get("shot_plan") or pkg.get("shots"))
    # Normalize legacy scene shape
    norm_scenes = []
    for i, s in enumerate(scenes):
        if not isinstance(s, dict):
            continue
        if s.get("scene_number") is not None:
            scene_number = int(s["scene_number"])
        elif s.get("index") is not None:
            scene_number = int(s["index"]) + 1
        else:
            scene_number = i + 1
        norm_scenes.append(
            {
                "scene_number": scene_number,
                "title": s.get("title") or f"Scene {i + 1}",
                "scene_purpose": s.get("description") or s.get("scene_purpose") or "",
                "estimated_duration_seconds": s.get("duration_seconds")
                or s.get("estimated_duration_seconds")
                or 3,
                "environment": s.get("environment") or "",
                "weather": s.get("weather") or "",
                "time": s.get("time") or "",
                "character_emotion": s.get("character_emotion") or "",
            }
        )
    norm_shots = []
    for i, sh in enumerate(shots):
        if not isinstance(sh, dict):
            continue
        cam = sh.get("camera") if isinstance(sh.get("camera"), dict) else {}
        scene_idx = int(sh.get("scene_index") or sh.get("scene_number") or 0)
        scene_number = scene_idx + 1 if "scene_index" in sh else max(1, scene_idx)
        if sh.get("scene_number"):
            scene_number = int(sh["scene_number"])
        norm_shots.append(
            {
                "scene_number": scene_number,
                "shot_number": int(
                    sh.get("shot_number") or (int(sh.get("shot_index") or 0) + 1) or (i + 1)
                ),
                "shot_type": cam.get("shot_type") or sh.get("shot_type") or sh.get("title") or "Medium Shot",
                "camera_angle": cam.get("camera_angle") or cam.get("angle") or "",
                "lens": cam.get("lens") or "",
                "camera_movement": cam.get("camera_movement") or cam.get("movement") or "",
                "lighting": cam.get("lighting") or [],
                "environment": sh.get("environment") or "",
                "weather": sh.get("weather") or "",
                "time": sh.get("time") or "",
                "character_emotion": sh.get("character_emotion") or "",
                "purpose": sh.get("description") or sh.get("purpose") or sh.get("action") or "",
                "estimated_duration_seconds": sh.get("duration_seconds")
                or sh.get("estimated_duration_seconds")
                or 3,
                "transition_type": sh.get("transition_type") or "cut",
                "composition": cam.get("composition") or "",
                "depth_of_field": cam.get("depth_of_field") or "",
                "color_palette": cam.get("color_palette") or [],
            }
        )
    prompt = str(pkg.get("prompt") or pkg.get("enhanced_prompt") or "")
    return norm_scenes, norm_shots, prompt


def _export_defaults(
    production_package: dict[str, Any] | None,
    production_render: dict[str, Any] | None,
) -> tuple[str, str, bool]:
    render = production_render or (production_package or {}).get("production_render") or {}
    specs = render.get("export_specs") or []
    if specs and isinstance(specs[0], dict):
        primary = next(
            (s for s in specs if s.get("format") == "mp4" and s.get("aspect") == "landscape"),
            specs[0],
        )
        return (
            str(primary.get("aspect") or "landscape"),
            str(primary.get("resolution") or "1080p"),
            bool(primary.get("hdr")),
        )
    manifest = render.get("video_manifest") or (production_package or {}).get("video_manifest") or {}
    export = manifest.get("export") if isinstance(manifest, dict) else {}
    if isinstance(export, dict) and export:
        return (
            str(export.get("aspect") or "landscape"),
            str(export.get("resolution") or "1080p"),
            bool(export.get("hdr")),
        )
    return "landscape", "1080p", False


def _ref_urls(character_memory: list[dict[str, Any]] | None) -> list[str]:
    urls: list[str] = []
    for c in character_memory or []:
        for u in c.get("reference_image_urls") or []:
            if isinstance(u, str) and u.strip():
                urls.append(u.strip())
    return urls


def map_production_package_to_job(
    production_package: dict[str, Any] | None,
    *,
    scene_breakdown: dict[str, Any] | None = None,
    character_memory: list[dict[str, Any]] | None = None,
    director_plan: dict[str, Any] | None = None,
    production_render: dict[str, Any] | None = None,
    visual_style: dict[str, Any] | None = None,
    parent_generation_id: str | None = None,
    provider_hint: str | None = None,
    max_attempts: int = 3,
) -> TextToVideoJob:
    pkg = dict(production_package or {})
    scenes_raw, shots_raw, prompt = _extract_scenes_shots(pkg, scene_breakdown)
    if not prompt:
        prompt = str(pkg.get("enhanced_prompt") or pkg.get("prompt") or "cinematic video")

    # If shots missing but scenes exist, synthesize one shot per scene.
    if scenes_raw and not shots_raw:
        shots_raw = []
        for s in scenes_raw:
            shots_raw.append(
                {
                    "scene_number": s.get("scene_number") or 1,
                    "shot_number": 1,
                    "shot_type": "Medium Shot",
                    "purpose": s.get("scene_purpose") or s.get("title") or "",
                    "estimated_duration_seconds": s.get("estimated_duration_seconds") or 3,
                    "environment": s.get("environment") or "",
                    "weather": s.get("weather") or "",
                    "time": s.get("time") or "",
                    "character_emotion": s.get("character_emotion") or "",
                }
            )

    aspect, resolution, hdr = _export_defaults(pkg, production_render)
    chars = list(character_memory or pkg.get("character_memory") or [])
    director = director_plan or pkg.get("director_plan") or {}
    director_notes = list(
        director.get("director_notes")
        or pkg.get("director_notes")
        or []
    )
    identity = identity_lock_from_memory(chars)
    refs = _ref_urls(chars)
    job_id = _job_id(parent_generation_id, prompt)
    ts = _now()

    scene_by_number: dict[int, dict[str, Any]] = {}
    scenes_meta: list[SceneMetadata] = []
    for s in scenes_raw:
        num = int(s.get("scene_number") or (len(scenes_meta) + 1))
        scene_by_number[num] = s
        sid = f"{job_id}_sc{num}"
        scenes_meta.append(
            SceneMetadata(
                scene_id=sid,
                scene_number=num,
                title=str(s.get("title") or f"Scene {num}"),
                purpose=str(s.get("scene_purpose") or s.get("purpose") or ""),
                duration_seconds=float(s.get("estimated_duration_seconds") or 3),
                environment=str(s.get("environment") or ""),
                weather=str(s.get("weather") or ""),
                time=str(s.get("time") or ""),
                character_emotion=str(s.get("character_emotion") or ""),
                shot_ids=[],
                extra={"raw_keys": sorted(s.keys())[:20]},
            )
        )
    scene_meta_by_num = {s.scene_number: s for s in scenes_meta}

    shots_meta: list[ShotMetadata] = []
    requests: list[ProviderGenerationRequest] = []

    for sh in shots_raw:
        scene_num = int(sh.get("scene_number") or 1)
        shot_num = int(sh.get("shot_number") or (len(shots_meta) + 1))
        shot_id = f"{job_id}_sc{scene_num}_sh{shot_num}"
        scene_id = f"{job_id}_sc{scene_num}"
        if scene_num in scene_meta_by_num:
            scene_meta_by_num[scene_num].shot_ids.append(shot_id)
        elif scene_num not in scene_by_number:
            # Orphan shot — create placeholder scene
            scenes_meta.append(
                SceneMetadata(
                    scene_id=scene_id,
                    scene_number=scene_num,
                    title=f"Scene {scene_num}",
                    purpose="",
                    duration_seconds=float(sh.get("estimated_duration_seconds") or 3),
                    shot_ids=[shot_id],
                )
            )
            scene_meta_by_num[scene_num] = scenes_meta[-1]
            scene_by_number[scene_num] = {}

        dur = float(sh.get("estimated_duration_seconds") or 3)
        shots_meta.append(
            ShotMetadata(
                shot_id=shot_id,
                scene_number=scene_num,
                shot_number=shot_num,
                shot_type=str(sh.get("shot_type") or "Medium Shot"),
                duration_seconds=dur,
                camera_angle=str(sh.get("camera_angle") or ""),
                lens=str(sh.get("lens") or ""),
                camera_movement=str(sh.get("camera_movement") or ""),
                lighting=list(sh.get("lighting") or []),
                environment=str(sh.get("environment") or ""),
                weather=str(sh.get("weather") or ""),
                time=str(sh.get("time") or ""),
                character_emotion=str(sh.get("character_emotion") or ""),
                purpose=str(sh.get("purpose") or ""),
                transition_type=str(sh.get("transition_type") or "cut"),
            )
        )

        scene_dict = scene_by_number.get(scene_num) or {}
        prompt_text = build_shot_prompt(
            base_prompt=prompt,
            shot=sh,
            scene=scene_dict,
            character_memory=chars,
            director_notes=director_notes,
            visual_style=visual_style or pkg.get("visual_style"),
        )
        req_id = f"{shot_id}_req"
        requests.append(
            ProviderGenerationRequest(
                request_id=req_id,
                job_id=job_id,
                scene_id=scene_id,
                shot_id=shot_id,
                scene_number=scene_num,
                shot_number=shot_num,
                prompt=prompt_text,
                duration_seconds=max(2.0, min(dur, 15.0)),
                provider_hint=provider_hint,
                aspect=aspect,
                resolution=resolution if resolution != "8k_ready" else "4k",
                hdr=hdr,
                negative_prompt=build_negative_prompt(sh),
                identity_lock=identity,
                reference_image_urls=list(refs),
                arguments={
                    "scene_number": scene_num,
                    "shot_number": shot_num,
                    "shot_type": sh.get("shot_type"),
                },
                metadata={
                    "transition_type": sh.get("transition_type") or "cut",
                    "source": "production_package",
                },
                state="planned",
                max_attempts=max_attempts,
            )
        )

    # Snapshot without huge nested render if present
    snapshot = {
        "prompt": prompt,
        "enhanced_prompt": pkg.get("enhanced_prompt"),
        "scene_count": len(scenes_meta),
        "shot_count": len(shots_meta),
        "has_scene_breakdown": bool(scene_breakdown or pkg.get("scene_breakdown")),
        "has_character_memory": bool(chars),
        "has_director_plan": bool(director),
    }

    return TextToVideoJob(
        job_id=job_id,
        parent_generation_id=parent_generation_id,
        prompt=prompt,
        state="planned",
        scenes=scenes_meta,
        shots=shots_meta,
        requests=requests,
        character_memory=chars,
        director_notes=director_notes,
        production_package_snapshot=snapshot,
        created_at=ts,
        updated_at=ts,
        metadata={
            "engine": "text_to_video",
            "version": "1.0",
            "aspect": aspect,
            "resolution": resolution,
            "hdr": hdr,
        },
    )
