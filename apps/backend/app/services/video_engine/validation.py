"""Production validation for end-to-end video readiness."""

from __future__ import annotations

from typing import Any

from app.services.video_engine.models import PipelineStage, ValidationResult


def validate_production(
    stages: list[PipelineStage],
    *,
    prompt: str,
    scenes: list[Any] | None,
    shots: list[Any] | None,
    cameras: list[Any] | None,
    production_render: dict[str, Any] | None,
    scene_render: dict[str, Any] | None,
    multi_gpu: dict[str, Any] | None,
    download_ready: bool,
    quality_overall: float,
) -> ValidationResult:
    checks: dict[str, bool] = {}
    issues: list[dict[str, Any]] = []
    blockers: list[str] = []
    warnings: list[str] = []

    def fail(key: str, msg: str, *, blocker: bool = True) -> None:
        checks[key] = False
        level = "error" if blocker else "warning"
        issues.append({"code": key, "level": level, "message": msg})
        if blocker:
            blockers.append(msg)
        else:
            warnings.append(msg)

    def ok(key: str) -> None:
        checks[key] = True

    if (prompt or "").strip():
        ok("has_prompt")
    else:
        fail("has_prompt", "Prompt is empty")

    if scenes:
        ok("has_scenes")
    else:
        fail("has_scenes", "No scenes planned")

    if shots:
        ok("has_shots")
    else:
        fail("has_shots", "No shots planned")

    if cameras or (scene_render and scene_render.get("job_id")):
        ok("has_camera")
    else:
        fail("has_camera", "No camera plan / camera motion", blocker=False)

    pr = production_render or {}
    validation = pr.get("validation") or {}
    if validation.get("passed"):
        ok("export_validated")
    elif pr.get("export_specs"):
        ok("export_specs_present")
        fail("export_validated", "Export specs present but validation not passed", blocker=False)
    else:
        fail("export_validated", "Export validation missing")

    if (scene_render or {}).get("job_id") or pr.get("video_manifest"):
        ok("has_render")
    else:
        fail("has_render", "No scene/production render package", blocker=False)

    if multi_gpu and (multi_gpu.get("assigned") or multi_gpu.get("workers")):
        ok("gpu_orchestrated")
    else:
        fail("gpu_orchestrated", "Multi GPU assignment missing", blocker=False)

    if download_ready:
        ok("download_ready")
    else:
        fail("download_ready", "Download package not ready")

    if quality_overall >= 0.75:
        ok("quality_threshold")
    else:
        fail(
            "quality_threshold",
            f"Quality score {quality_overall:.2f} below production threshold 0.75",
        )

    failed_stages = [s.name for s in stages if s.status == "failed"]
    critical = {"prompt", "director", "scene", "shot", "export"}
    critical_fails = [n for n in failed_stages if n in critical]
    if critical_fails:
        fail(
            "critical_stages",
            f"Critical stages failed: {', '.join(critical_fails)}",
        )
    else:
        ok("critical_stages")

    passed = not blockers
    return ValidationResult(
        passed=passed,
        checks=checks,
        issues=issues,
        blockers=blockers,
        warnings=warnings,
    )
