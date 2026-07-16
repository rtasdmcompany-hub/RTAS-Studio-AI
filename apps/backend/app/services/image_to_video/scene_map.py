"""Map images onto production scenes for I2V requests."""

from __future__ import annotations

from typing import Any

from app.services.image_to_video.models import ImageAsset, SceneImageBinding


def _pick_primary(images: list[ImageAsset]) -> ImageAsset | None:
    priority = ("character", "single", "product", "multiple", "reference", "logo")
    by_role = {r: [] for r in priority}
    for img in images:
        by_role.setdefault(img.role, []).append(img)
    for role in priority:
        if by_role.get(role):
            return by_role[role][0]
    return images[0] if images else None


def _refs_for_scene(
    images: list[ImageAsset],
    primary: ImageAsset,
    *,
    scene_index: int,
) -> list[str]:
    refs: list[str] = []
    multi = [i for i in images if i.role == "multiple"]
    if multi:
        # Round-robin extra frames as soft refs
        for i, img in enumerate(multi):
            if img.image_id == primary.image_id:
                continue
            if i % max(1, len(multi)) == scene_index % max(1, len(multi)):
                refs.append(img.image_id)
    for img in images:
        if img.image_id == primary.image_id:
            continue
        if img.role in ("reference", "character", "product", "logo") and img.image_id not in refs:
            refs.append(img.image_id)
    return refs[:6]


def extract_scenes(
    production_package: dict[str, Any] | None,
    scene_breakdown: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    pkg = production_package or {}
    breakdown = scene_breakdown or pkg.get("scene_breakdown") or {}
    production = breakdown.get("Production") if isinstance(breakdown, dict) else None
    if isinstance(production, dict) and production.get("Scenes"):
        return list(production["Scenes"])
    scenes = pkg.get("scene_plan") or pkg.get("scenes") or []
    out = []
    for i, s in enumerate(scenes):
        if not isinstance(s, dict):
            continue
        out.append(
            {
                "scene_number": s.get("scene_number")
                or ((int(s["index"]) + 1) if s.get("index") is not None else i + 1),
                "title": s.get("title") or f"Scene {i + 1}",
                "scene_purpose": s.get("description") or s.get("scene_purpose") or "",
                "estimated_duration_seconds": s.get("duration_seconds")
                or s.get("estimated_duration_seconds")
                or 4,
                "environment": s.get("environment") or "",
                "weather": s.get("weather") or "",
                "time": s.get("time") or "",
            }
        )
    return out


def extract_shots(
    production_package: dict[str, Any] | None,
    scene_breakdown: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    pkg = production_package or {}
    breakdown = scene_breakdown or pkg.get("scene_breakdown") or {}
    production = breakdown.get("Production") if isinstance(breakdown, dict) else None
    if isinstance(production, dict) and production.get("Shots"):
        return list(production["Shots"])
    return list(pkg.get("shot_plan") or pkg.get("shots") or [])


def map_images_to_scenes(
    images: list[ImageAsset],
    scenes: list[dict[str, Any]],
    *,
    job_id: str,
) -> list[SceneImageBinding]:
    if not images:
        return []
    primary = _pick_primary(images)
    if primary is None:
        return []

    if not scenes:
        scenes = [
            {
                "scene_number": 1,
                "title": "Primary Image Motion",
                "scene_purpose": "Animate source image",
                "estimated_duration_seconds": 5,
            }
        ]

    bindings: list[SceneImageBinding] = []
    multi = [i for i in images if i.role == "multiple"]
    for i, scene in enumerate(scenes):
        num = int(scene.get("scene_number") or (i + 1))
        # For multiple stills, advance primary across sequence when available
        scene_primary = primary
        if multi:
            scene_primary = multi[min(i, len(multi) - 1)]
        bindings.append(
            SceneImageBinding(
                scene_number=num,
                scene_id=f"{job_id}_sc{num}",
                primary_image_id=scene_primary.image_id,
                reference_image_ids=_refs_for_scene(images, scene_primary, scene_index=i),
                notes=[
                    f"Primary role={scene_primary.role}",
                    f"Scene={scene.get('title') or num}",
                ],
            )
        )
    return bindings
