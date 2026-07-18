"""Phase 5 Sprint 10 — Final production release engine."""

from __future__ import annotations

from typing import Any

from app.services.final_release.pipeline import run_release_pipeline
from app.services.final_release.quality import score_production
from app.services.final_release.stress import run_all_stress_batches, run_stress_batch
from app.services.final_release.version import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    FINAL_RELEASE,
    PHASE,
    PHASE_STATUS,
    READY_FOR_PHASE_6,
    SPRINT,
    STRESS_BATCHES,
)


def verify_release(
    prompt: str = "Cinematic final release — hero faces conflict then finds hope at golden hour.",
    **kwargs: Any,
) -> dict[str, Any]:
    result = run_release_pipeline(prompt, **kwargs)
    return {
        **result,
        "phase": PHASE,
        "sprint": SPRINT,
        "final_release": FINAL_RELEASE,
        "phase_status": PHASE_STATUS,
        "ready_for_phase_6": READY_FOR_PHASE_6 and result.get("ok"),
    }


def stress_release(
    *,
    batches: tuple[int, ...] | list[int] | None = None,
    max_jobs: int | None = None,
) -> dict[str, Any]:
    batch_tuple = tuple(batches) if batches else STRESS_BATCHES
    result = run_all_stress_batches(batch_tuple, max_jobs=max_jobs)
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
        "operation": "stress",
        "phase": PHASE,
        "sprint": SPRINT,
        **result,
    }


def final_report(
    *,
    prompt: str | None = None,
    run_stress: bool = False,
    stress_max_jobs: int | None = 25,
) -> dict[str, Any]:
    verification = verify_release(
        prompt
        or "Final Phase 5 cinematic production — short film with emotional climax and clear resolution."
    )
    stress = None
    if run_stress:
        stress = stress_release(max_jobs=stress_max_jobs)

    quality = verification.get("quality") or {}
    modules = [
        "AI Director",
        "Scene Director",
        "Shot Director",
        "Camera Director",
        "Character Director",
        "Story Director",
        "Production Planner",
        "Director Memory",
        "World Engine Integration",
        "Emotion Engine Integration",
        "Motion Engine Integration",
        "Audio Planner",
        "Video Engine",
        "Renderer",
        "Exporter",
        "Download Package",
        "Quality Scoring",
        "Retry System",
        "Analytics",
        "Production Monitoring",
        "Final Release Pipeline",
    ]

    phase5_complete = bool(
        verification.get("ok")
        and quality.get("passed")
        and (stress is None or stress.get("all_passed"))
    )

    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
        "final_version": f"{ENGINE_NAME} v{ENGINE_VERSION}",
        "phase": PHASE,
        "sprint": SPRINT,
        "final_release": FINAL_RELEASE,
        "phase_status": "COMPLETE" if phase5_complete else "INCOMPLETE",
        "ready_for_phase_6": phase5_complete,
        "modules_completed": modules,
        "verification": verification.get("verification"),
        "pipeline_stages": verification.get("pipeline_stages"),
        "quality_score": quality,
        "overall_production_score": quality.get("overall_production_score"),
        "stress": stress,
        "director_job_id": verification.get("director_job_id"),
        "video_job_id": verification.get("video_job_id"),
        "export_job_id": verification.get("export_job_id"),
        "processing_time_ms": verification.get("processing_time_ms"),
        "ok": phase5_complete,
        "mark": "✅ PHASE 5 COMPLETE" if phase5_complete else "PHASE 5 INCOMPLETE",
        "next": "✅ READY FOR PHASE 6" if phase5_complete else "FIX FAILURES BEFORE PHASE 6",
    }


def verify_dict(**kwargs: Any) -> dict[str, Any]:
    return verify_release(**kwargs)


def report_dict(**kwargs: Any) -> dict[str, Any]:
    return final_report(**kwargs)


def stress_dict(**kwargs: Any) -> dict[str, Any]:
    return stress_release(**kwargs)


# re-exports for tests
__all__ = [
    "verify_release",
    "stress_release",
    "final_report",
    "run_stress_batch",
    "score_production",
    "verify_dict",
    "report_dict",
    "stress_dict",
]
