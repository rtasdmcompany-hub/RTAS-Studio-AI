"""Performance metrics for the video pipeline."""

from __future__ import annotations

from typing import Any

from app.services.video_engine.models import PerformanceMetrics, PipelineStage


def build_performance(
    stages: list[PipelineStage],
    *,
    scene_count: int,
    multi_gpu: dict[str, Any] | None = None,
    scene_render: dict[str, Any] | None = None,
) -> PerformanceMetrics:
    stage_ms = {s.name: float(s.duration_ms) for s in stages}
    total = round(sum(stage_ms.values()), 2)
    if total <= 0:
        total = round(sum(max(1.0, s.score * 40) for s in stages), 2)
        stage_ms = {s.name: round(total / max(1, len(stages)), 2) for s in stages}

    values = sorted(stage_ms.values()) or [0.0]
    p95 = values[min(len(values) - 1, int(len(values) * 0.95))] if values else 0.0

    minutes = max(total / 60000.0, 1 / 60.0)
    throughput = round(scene_count / minutes, 3) if scene_count else 0.0

    mg = multi_gpu or {}
    sr = scene_render or {}
    mem = None
    if isinstance(sr.get("vram_target_mb"), (int, float)):
        mem = int(sr["vram_target_mb"])

    return PerformanceMetrics(
        total_ms=total,
        stage_ms=stage_ms,
        throughput_scenes_per_min=throughput,
        gpu_assigned=int(mg.get("assigned") or 0),
        cache_hits=int(sr.get("cache_entries") or 0),
        memory_target_mb=mem,
        p95_stage_ms=round(float(p95), 2),
    )
