"""
RTAS Studio AI — Video Engine v1.0

Complete end-to-end production video pipeline:
Prompt → Director → Scene → Shot → Camera → Generation → Rendering → Export → Download

Includes performance, monitoring, analytics, production validation,
stress testing, error recovery, automatic retry, and quality scoring.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any
from uuid import uuid4

from app.services.video_engine.analytics import build_analytics
from app.services.video_engine.download import build_download_package
from app.services.video_engine.models import StressTestResult, VideoEnginePlan
from app.services.video_engine.monitoring import build_monitoring
from app.services.video_engine.performance import build_performance
from app.services.video_engine.quality import build_quality_score
from app.services.video_engine.recovery import apply_automatic_retry
from app.services.video_engine.stages import PIPELINE_ORDER, evaluate_stages
from app.services.video_engine.store import get_plan as store_get
from app.services.video_engine.store import put_plan
from app.services.video_engine.stress import run_stress_test
from app.services.video_engine.validation import validate_production
from app.services.video_engine.version import ENGINE_LABEL, ENGINE_NAME, ENGINE_VERSION

logger = logging.getLogger(__name__)


def _job_id(prompt: str) -> str:
    seed = f"{ENGINE_VERSION}|{prompt}|{uuid4().hex[:8]}"
    return f"videoeng_{hashlib.sha1(seed.encode('utf-8')).hexdigest()[:10]}"


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def build_video_engine_plan(
    prompt: str,
    *,
    intelligence: dict[str, Any] | None = None,
    director_plan: dict[str, Any] | None = None,
    scenes: list[Any] | None = None,
    shots: list[Any] | None = None,
    cameras: list[Any] | None = None,
    character_memory: list[Any] | None = None,
    cinematic_quality: dict[str, Any] | None = None,
    character_consistency: dict[str, Any] | None = None,
    production_render: dict[str, Any] | None = None,
    scene_render: dict[str, Any] | None = None,
    camera_motion: dict[str, Any] | None = None,
    physics: dict[str, Any] | None = None,
    multi_gpu: dict[str, Any] | None = None,
    text_to_video: dict[str, Any] | None = None,
    auto_retry: bool = True,
    run_stress: bool = True,
    stress_iterations: int = 3,
    parent_generation_id: str | None = None,
) -> VideoEnginePlan:
    text = (prompt or "").strip() or "Untitled production"
    intel = intelligence or {}
    director = director_plan or intel.get("director_plan") or {}
    scene_list = scenes or _as_list(intel.get("scenes"))
    shot_list = shots or _as_list(intel.get("shots"))
    camera_list = cameras or _as_list(intel.get("cameras"))
    pr = production_render or intel.get("production_render") or {}
    export_validated = bool((pr.get("validation") or {}).get("passed"))

    # First-pass download readiness estimate (refined after quality)
    prelim_download = build_download_package(
        prompt=text,
        production_render=pr,
        job_id="prelim",
        quality_overall=0.8,
        export_validated=export_validated,
    )

    stages = evaluate_stages(
        prompt=text,
        intelligence=intel,
        director_plan=director,
        scenes=scene_list,
        shots=shot_list,
        cameras=camera_list,
        camera_motion=camera_motion,
        generation=text_to_video,
        scene_render=scene_render,
        production_render=pr,
        multi_gpu=multi_gpu,
        t2v=text_to_video,
        download_ready=prelim_download.ready,
    )

    stages, recovery = apply_automatic_retry(stages, auto_retry=auto_retry)

    quality = build_quality_score(
        stages,
        cinematic_quality=cinematic_quality or intel.get("cinematic_quality"),
        character_consistency=character_consistency
        or intel.get("character_consistency"),
        production_render=pr,
        scene_render=scene_render,
    )

    download = build_download_package(
        prompt=text,
        production_render=pr,
        job_id="pending",
        quality_overall=quality.overall,
        export_validated=export_validated,
    )
    # Re-align download stage with final readiness
    for s in stages:
        if s.name == "download":
            if download.ready:
                s.status = "passed"
                s.score = max(s.score, 0.9)
                s.errors = []
            elif s.status == "failed" and auto_retry:
                s.status = "recovered"
                s.notes.append("download waiting on export gate")

    validation = validate_production(
        stages,
        prompt=text,
        scenes=scene_list,
        shots=shot_list,
        cameras=camera_list,
        production_render=pr,
        scene_render=scene_render,
        multi_gpu=multi_gpu,
        download_ready=download.ready,
        quality_overall=quality.overall,
    )

    # Production ready = validation + quality gate
    production_ready = bool(
        validation.passed and quality.production_ready and download.ready
    )
    quality.production_ready = production_ready

    performance = build_performance(
        stages,
        scene_count=len(scene_list),
        multi_gpu=multi_gpu,
        scene_render=scene_render,
    )
    monitoring = build_monitoring(
        stages,
        validation,
        retry_total=sum(s.retries for s in stages) + len(recovery.pending_retries),
    )
    analytics = build_analytics(
        scenes=scene_list,
        shots=shot_list,
        cameras=camera_list,
        character_memory=character_memory or intel.get("character_memory"),
        physics=physics,
        camera_motion=camera_motion,
        multi_gpu=multi_gpu,
        production_render=pr,
        quality_overall=quality.overall,
        production_ready=production_ready,
    )

    job_id = _job_id(text)
    download.primary_url_hint = f"/api/video-engine/download/{job_id}"
    # embed job id in filename
    download.filename = f"rtas_video_{job_id[-8:]}.mp4"

    if run_stress:
        stress_result = run_stress_test(
            build_video_engine_plan,
            iterations=stress_iterations,
            kwargs={
                "prompt": text,
                "intelligence": intel,
                "director_plan": director,
                "scenes": scene_list,
                "shots": shot_list,
                "cameras": camera_list,
                "character_memory": character_memory,
                "cinematic_quality": cinematic_quality,
                "character_consistency": character_consistency,
                "production_render": pr,
                "scene_render": scene_render,
                "camera_motion": camera_motion,
                "physics": physics,
                "multi_gpu": multi_gpu,
                "text_to_video": text_to_video,
                "auto_retry": auto_retry,
            },
        )
    else:
        stress_result = StressTestResult(
            ran=False,
            iterations=0,
            success_rate=1.0,
            avg_ms=0.0,
            max_ms=0.0,
            failures=0,
            notes=["stress skipped"],
        )

    timeline = []
    t = 0.0
    for s in stages:
        timeline.append(
            {
                "t": round(t, 3),
                "stage": s.name,
                "status": s.status,
                "score": s.score,
                "order": s.order,
            }
        )
        t += 1.0

    directives = [
        f"{ENGINE_LABEL} — production end-to-end pipeline.",
        f"Flow: {' → '.join(PIPELINE_ORDER)}.",
        f"Quality {quality.overall:.2f} ({quality.grade}); production_ready={production_ready}.",
        f"Validation passed={validation.passed}; download_ready={download.ready}.",
        f"Monitoring: {monitoring.pipeline_status}; alerts={len(monitoring.active_alerts)}.",
        f"Auto-retry={recovery.auto_retry}; recovered={recovery.recovered_stages}.",
    ]
    if stress_result.ran:
        directives.append(
            f"Stress: {stress_result.iterations} iters success={stress_result.success_rate}"
        )

    integrations = {
        "director": bool(director),
        "scene_render": (scene_render or {}).get("job_id"),
        "multi_gpu": (multi_gpu or {}).get("job_id"),
        "camera_motion": (camera_motion or {}).get("job_id"),
        "physics": (physics or {}).get("job_id"),
        "text_to_video": (text_to_video or {}).get("job_id"),
        "export_validated": export_validated,
        "parent_generation_id": parent_generation_id,
    }

    plan = VideoEnginePlan(
        job_id=job_id,
        engine=ENGINE_NAME,
        version=ENGINE_VERSION,
        prompt=text[:2000],
        stages=stages,
        quality=quality,
        validation=validation,
        performance=performance,
        monitoring=monitoring,
        analytics=analytics,
        recovery=recovery,
        stress=stress_result,
        download=download,
        timeline=timeline,
        integrations=integrations,
        provider_directives=directives,
        production_ready=production_ready,
    )
    put_plan(plan)
    logger.info(
        "video_engine_ready %s job=%s ready=%s quality=%.3f grade=%s",
        ENGINE_LABEL,
        plan.job_id,
        production_ready,
        quality.overall,
        quality.grade,
    )
    return plan


def build_video_engine_dict(prompt: str, **kwargs: Any) -> dict[str, Any]:
    plan = build_video_engine_plan(prompt, **kwargs)
    return {
        "plan": plan.to_dict(),
        "summary": plan.summary(),
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
    }


def get_plan(job_id: str) -> VideoEnginePlan | None:
    return store_get(job_id)
