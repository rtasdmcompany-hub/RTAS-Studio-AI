"""Enterprise AI Orchestration Platform facade — final Phase 6 release."""

from __future__ import annotations

from typing import Any

from app.services.enterprise_platform import pipeline, quality, registry, stress
from app.services.enterprise_platform.models import PlatformRelease, new_id
from app.services.enterprise_platform.version import (
    INTEGRATED_ENGINES,
    PHASE,
    PLATFORM_LABEL,
    PLATFORM_NAME,
    PLATFORM_VERSION,
    RELEASE_STATUS,
    REQUIRED_PROVIDERS,
    SPRINT,
)

_last_quality: dict[str, Any] | None = None
_last_stress: dict[str, Any] | None = None
_last_pipeline: dict[str, Any] | None = None
_release: PlatformRelease | None = None


class EnterprisePlatformEngine:
    def status(self) -> dict[str, Any]:
        providers = registry.verify_providers()
        engines = registry.verify_engines()
        return {
            "ok": providers.get("ok") and engines.get("ok"),
            "platform": PLATFORM_NAME,
            "version": PLATFORM_VERSION,
            "label": PLATFORM_LABEL,
            "phase": PHASE,
            "sprint": SPRINT,
            "release_status": RELEASE_STATUS,
            "providers": providers,
            "engines": engines,
            "required_providers": list(REQUIRED_PROVIDERS),
            "integrated_engines": list(INTEGRATED_ENGINES),
            "pipeline_contract": [
                "prompt",
                "ai_router",
                "provider_selection",
                "memory_engine",
                "context_engine",
                "workflow_engine",
                "queue_engine",
                "provider_execution",
                "monitoring",
                "quality_validation",
                "export",
                "download",
            ],
        }

    def validate(self, *, prompt: str | None = None) -> dict[str, Any]:
        global _last_pipeline, _last_quality
        pipe = pipeline.run_pipeline(prompt=prompt or "Enterprise platform final validation run")
        _last_pipeline = pipe
        score = quality.generate_quality_score()
        _last_quality = score.to_dict()
        pipe_ratio = pipe["passed_steps"] / max(1, pipe["total_steps"])
        return {
            "ok": score.passed and pipe_ratio >= 0.9,
            "platform": PLATFORM_NAME,
            "version": PLATFORM_VERSION,
            "pipeline": pipe,
            "quality": score.to_dict(),
        }

    def quality_report(self) -> dict[str, Any]:
        global _last_quality
        if _last_quality is None:
            _last_quality = quality.generate_quality_score().to_dict()
        return {
            "ok": bool(_last_quality.get("passed")),
            "platform": PLATFORM_NAME,
            "version": PLATFORM_VERSION,
            "quality": _last_quality,
            "enterprise_quality_score": _last_quality.get("overall"),
        }

    def stress_test(self, counts: list[int] | None = None) -> dict[str, Any]:
        global _last_stress
        result = stress.run_stress(counts=counts)
        _last_stress = result
        return {
            "ok": result.get("ok"),
            "platform": PLATFORM_NAME,
            "version": PLATFORM_VERSION,
            **result,
        }

    def release(self) -> dict[str, Any]:
        global _release, _last_quality, _last_stress, _last_pipeline
        if _last_quality is None:
            _last_quality = quality.generate_quality_score().to_dict()
        if _last_pipeline is None:
            _last_pipeline = pipeline.run_pipeline()
        score = float(_last_quality.get("overall") or 0)
        pipe_ratio = (
            _last_pipeline.get("passed_steps", 0) / max(1, _last_pipeline.get("total_steps", 1))
        )
        release_ready = bool(_last_quality.get("passed")) and pipe_ratio >= 0.9
        _release = PlatformRelease(
            release_id=new_id("rel"),
            platform=PLATFORM_NAME,
            version=PLATFORM_VERSION,
            phase=PHASE,
            sprint=SPRINT,
            status=RELEASE_STATUS if release_ready else "PENDING",
            quality_score=score,
        )
        return {
            "ok": _release.status == RELEASE_STATUS,
            "release": _release.to_dict(),
            "quality": _last_quality,
            "pipeline_ok": pipe_ratio >= 0.9,
            "pipeline_ratio": round(pipe_ratio, 4),
            "stress": _last_stress,
            "message": (
                "RTAS Studio AI Enterprise AI Orchestration Platform v1.0 RELEASED"
                if _release.status == RELEASE_STATUS
                else "Release pending quality/pipeline gates"
            ),
        }


_engine: EnterprisePlatformEngine | None = None


def get_platform_engine() -> EnterprisePlatformEngine:
    global _engine
    if _engine is None:
        _engine = EnterprisePlatformEngine()
    return _engine


def reset_engine() -> None:
    global _engine, _last_quality, _last_stress, _last_pipeline, _release
    _engine = None
    _last_quality = None
    _last_stress = None
    _last_pipeline = None
    _release = None
