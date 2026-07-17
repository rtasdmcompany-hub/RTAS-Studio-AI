"""End-to-end pipeline stage graph: Prompt → … → Download."""

from __future__ import annotations

import time
from typing import Any

from app.services.video_engine.models import PipelineStage, StageName, StageStatus

PIPELINE_ORDER: tuple[StageName, ...] = (
    "prompt",
    "director",
    "scene",
    "shot",
    "camera",
    "generation",
    "rendering",
    "export",
    "download",
)


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (list, dict, str)):
        return bool(value)
    return True


def evaluate_stages(
    *,
    prompt: str,
    intelligence: dict[str, Any] | None,
    director_plan: dict[str, Any] | None,
    scenes: list[Any] | None,
    shots: list[Any] | None,
    cameras: list[Any] | None,
    camera_motion: dict[str, Any] | None,
    generation: dict[str, Any] | None,
    scene_render: dict[str, Any] | None,
    production_render: dict[str, Any] | None,
    multi_gpu: dict[str, Any] | None,
    t2v: dict[str, Any] | None,
    download_ready: bool,
) -> list[PipelineStage]:
    """Derive stage readiness from available pipeline artifacts."""
    intel = intelligence or {}
    director = director_plan or {}
    pr = production_render or {}
    sr = scene_render or {}
    gen = generation or t2v or {}
    cam = camera_motion or {}
    mg = multi_gpu or {}

    started = time.perf_counter()

    def elapsed() -> float:
        return round((time.perf_counter() - started) * 1000, 2)

    checks: list[tuple[StageName, bool, float, list[str], list[str], list[str]]] = [
        (
            "prompt",
            bool((prompt or "").strip()) or _present(intel.get("enhancement") or intel.get("prompt_understanding")),
            0.9 if (prompt or "").strip() else 0.2,
            ["raw_prompt"],
            ["enhanced_prompt", "prompt_understanding"],
            [],
        ),
        (
            "director",
            _present(director) or _present(intel.get("director_plan")),
            0.85 if _present(director) else 0.3,
            ["prompt"],
            ["director_plan", "cinematic_rhythm"],
            [],
        ),
        (
            "scene",
            bool(scenes) or _present(intel.get("scenes") or intel.get("scene_breakdown")),
            0.9 if scenes else 0.35,
            ["director"],
            ["scenes", "scene_breakdown"],
            [],
        ),
        (
            "shot",
            bool(shots) or _present(intel.get("shots")),
            0.88 if shots else 0.35,
            ["scene"],
            ["shots"],
            [],
        ),
        (
            "camera",
            bool(cameras) or _present(cam) or _present(intel.get("cameras")),
            0.87 if (cameras or cam) else 0.35,
            ["shot"],
            ["cameras", "camera_motion"],
            [],
        ),
        (
            "generation",
            _present(gen) or _present(t2v) or _present(mg.get("assigned")),
            0.8 if (gen or t2v or mg) else 0.25,
            ["camera"],
            ["text_to_video", "multi_gpu"],
            [],
        ),
        (
            "rendering",
            _present(sr) or _present(pr.get("video_manifest")),
            0.85 if (sr or pr.get("video_manifest")) else 0.3,
            ["generation"],
            ["scene_render", "video_manifest"],
            [],
        ),
        (
            "export",
            bool((pr.get("validation") or {}).get("passed"))
            or _present(pr.get("export_specs")),
            0.9 if (pr.get("validation") or {}).get("passed") else (0.55 if pr.get("export_specs") else 0.25),
            ["rendering"],
            ["export_specs", "validation"],
            [],
        ),
        (
            "download",
            download_ready,
            0.9 if download_ready else 0.4,
            ["export"],
            ["download_package"],
            [],
        ),
    ]

    stages: list[PipelineStage] = []
    for i, (name, ok, score, inputs, outputs, errors) in enumerate(checks):
        status: StageStatus = "passed" if ok else "failed"
        # Soft-fail early stages if later ones exist (partial plans)
        if not ok and name in ("generation", "download") and any(
            c[1] for c in checks[i + 1 :]
        ):
            status = "pending"
        notes = []
        if ok:
            notes.append(f"{name} artifacts present")
        else:
            notes.append(f"{name} incomplete — awaiting artifacts")
            if not errors:
                errors = [f"missing_{name}_artifacts"]
        stages.append(
            PipelineStage(
                name=name,
                order=i,
                status=status,
                duration_ms=elapsed() / max(1, len(checks)),
                score=round(score, 3),
                inputs=inputs,
                outputs=outputs,
                errors=errors if status == "failed" else [],
                notes=notes,
            )
        )
    return stages
