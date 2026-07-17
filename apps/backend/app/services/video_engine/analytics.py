"""Analytics snapshot for production video runs."""

from __future__ import annotations

from typing import Any

from app.services.video_engine.models import AnalyticsSnapshot


def build_analytics(
    *,
    scenes: list[Any] | None,
    shots: list[Any] | None,
    cameras: list[Any] | None,
    character_memory: list[Any] | None,
    physics: dict[str, Any] | None,
    camera_motion: dict[str, Any] | None,
    multi_gpu: dict[str, Any] | None,
    production_render: dict[str, Any] | None,
    quality_overall: float,
    production_ready: bool,
) -> AnalyticsSnapshot:
    effects = list((physics or {}).get("effects") or [])
    motions = list((camera_motion or {}).get("primary_motions") or [])
    skus = list((multi_gpu or {}).get("skus") or [])
    specs = (production_render or {}).get("export_specs") or []
    formats: list[str] = []
    for s in specs:
        if isinstance(s, dict) and s.get("format"):
            formats.append(str(s["format"]))
        elif hasattr(s, "format"):
            formats.append(str(getattr(s, "format")))
    if not formats:
        formats = ["mp4", "mov", "webm"]

    return AnalyticsSnapshot(
        scenes=len(scenes or []),
        shots=len(shots or []),
        cameras=len(cameras or []),
        characters=len(character_memory or []),
        effects=[str(e) for e in effects][:16],
        camera_motions=[str(m) for m in motions][:16],
        gpu_skus=[str(s) for s in skus][:12],
        export_formats=formats[:8],
        quality_overall=quality_overall,
        production_ready=production_ready,
    )
