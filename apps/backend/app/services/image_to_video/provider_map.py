"""Map I2V scene bindings to provider generation requests."""

from __future__ import annotations

from typing import Any

from app.services.image_to_video.models import (
    I2VProviderRequest,
    ImageAsset,
    SceneImageBinding,
)
from app.services.image_to_video.prompts import build_negative_prompt, merge_i2v_prompt


def _uri_by_id(images: list[ImageAsset]) -> dict[str, str]:
    return {i.image_id: i.resolved_uri for i in images if i.resolved_uri}


def _shot_for_scene(shots: list[dict[str, Any]], scene_number: int) -> dict[str, Any]:
    for sh in shots:
        sn = sh.get("scene_number")
        if sn is None and sh.get("scene_index") is not None:
            sn = int(sh["scene_index"]) + 1
        if int(sn or 0) == scene_number:
            return sh
    return {}


def build_provider_requests(
    *,
    job_id: str,
    motion_prompt: str,
    images: list[ImageAsset],
    bindings: list[SceneImageBinding],
    scenes: list[dict[str, Any]],
    shots: list[dict[str, Any]] | None = None,
    character_memory: list[dict[str, Any]] | None = None,
    director_notes: list[str] | None = None,
    preserve: dict[str, bool] | None = None,
    provider_hint: str | None = None,
    aspect: str = "landscape",
    resolution: str = "1080p",
    max_attempts: int = 3,
) -> list[I2VProviderRequest]:
    preserve = preserve or {
        "identity": True,
        "lighting": True,
        "composition": True,
        "environment": True,
    }
    uri_map = _uri_by_id(images)
    scene_by_num = {int(s.get("scene_number") or i + 1): s for i, s in enumerate(scenes)}
    shots = shots or []
    requests: list[I2VProviderRequest] = []

    for binding in bindings:
        scene = scene_by_num.get(binding.scene_number) or {
            "scene_number": binding.scene_number
        }
        shot = _shot_for_scene(shots, binding.scene_number)
        primary_uri = uri_map.get(binding.primary_image_id, "")
        if not primary_uri:
            continue
        ref_uris = [
            uri_map[rid]
            for rid in binding.reference_image_ids
            if rid in uri_map and uri_map[rid] != primary_uri
        ]
        # Include character/product/logo URLs even if not in binding refs
        for img in images:
            if img.role in ("character", "product", "logo") and img.resolved_uri:
                if img.resolved_uri not in ref_uris and img.resolved_uri != primary_uri:
                    ref_uris.append(img.resolved_uri)

        prompt = merge_i2v_prompt(
            motion_prompt=motion_prompt,
            images=images,
            scene=scene,
            shot=shot,
            character_memory=character_memory,
            preserve_identity=bool(preserve.get("identity", True)),
            preserve_lighting=bool(preserve.get("lighting", True)),
            preserve_composition=bool(preserve.get("composition", True)),
            preserve_environment=bool(preserve.get("environment", True)),
            director_notes=director_notes,
        )
        dur = float(
            shot.get("estimated_duration_seconds")
            or scene.get("estimated_duration_seconds")
            or 4
        )
        shot_number = int(shot.get("shot_number") or 1)
        req_id = f"{job_id}_sc{binding.scene_number}_sh{shot_number}_i2v"
        requests.append(
            I2VProviderRequest(
                request_id=req_id,
                job_id=job_id,
                scene_number=binding.scene_number,
                shot_number=shot_number,
                prompt=prompt,
                duration_seconds=max(2.0, min(dur, 15.0)),
                primary_image_url=primary_uri,
                reference_image_urls=ref_uris[:8],
                provider_hint=provider_hint,
                model_hint="image-to-video",
                aspect=aspect,
                resolution=resolution,
                negative_prompt=build_negative_prompt(
                    preserve_identity=bool(preserve.get("identity", True))
                ),
                arguments={
                    "preserve_identity": bool(preserve.get("identity", True)),
                    "preserve_lighting": bool(preserve.get("lighting", True)),
                    "preserve_composition": bool(preserve.get("composition", True)),
                    "preserve_environment": bool(preserve.get("environment", True)),
                },
                metadata={
                    "scene_id": binding.scene_id,
                    "primary_image_id": binding.primary_image_id,
                    "reference_image_ids": list(binding.reference_image_ids),
                    "mode": "image-to-video",
                },
                state="planned",
                max_attempts=max_attempts,
            )
        )
    return requests
