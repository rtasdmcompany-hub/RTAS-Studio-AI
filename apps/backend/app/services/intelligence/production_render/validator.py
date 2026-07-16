"""Export validation — ensure production package is delivery-ready."""

from __future__ import annotations

from typing import Any

from app.services.intelligence.production_render.models import (
    ExportSpec,
    ExportValidation,
    ValidationIssue,
    VideoManifest,
)


def validate_export_package(
    *,
    scenes: list[dict[str, Any]],
    shots: list[dict[str, Any]],
    timeline: dict[str, Any],
    captions: list[Any],
    subtitle_file: str,
    export_specs: list[ExportSpec],
    video_manifest: VideoManifest,
    voice_package: dict[str, Any],
    music_package: dict[str, Any],
    camera_plan: list[dict[str, Any]],
    director_notes: list[str],
) -> ExportValidation:
    issues: list[ValidationIssue] = []
    checks: dict[str, bool] = {}

    checks["has_scenes"] = bool(scenes)
    if not scenes:
        issues.append(
            ValidationIssue("missing_scenes", "error", "No scenes in production package")
        )

    checks["has_shots"] = bool(shots)
    if not shots:
        issues.append(
            ValidationIssue("missing_shots", "error", "No shots in production package")
        )

    runtime = float(
        timeline.get("total_duration_seconds")
        or video_manifest.runtime_seconds
        or 0
    )
    checks["runtime_positive"] = runtime > 0
    if runtime <= 0:
        issues.append(
            ValidationIssue("invalid_runtime", "error", "Runtime must be > 0")
        )

    checks["has_export_specs"] = bool(export_specs)
    formats = {s.format for s in export_specs}
    for required in ("mp4", "mov", "webm"):
        key = f"export_{required}"
        checks[key] = required in formats
        if required not in formats:
            issues.append(
                ValidationIssue(
                    key, "warning", f"Missing {required.upper()} export spec"
                )
            )

    aspects = {s.aspect for s in export_specs}
    for aspect in ("vertical", "landscape", "square"):
        checks[f"aspect_{aspect}"] = aspect in aspects

    checks["has_4k_or_higher"] = any(
        s.resolution in ("4k", "8k_ready") for s in export_specs
    )
    checks["has_8k_ready"] = any(s.resolution == "8k_ready" for s in export_specs)
    if not checks["has_8k_ready"]:
        issues.append(
            ValidationIssue("missing_8k_ready", "info", "No 8K-ready master spec")
        )

    checks["has_subtitles"] = bool(subtitle_file.strip()) and bool(captions)
    if not checks["has_subtitles"]:
        issues.append(
            ValidationIssue("missing_subtitles", "warning", "Subtitle/SRT file empty")
        )

    checks["has_voice_package"] = bool(voice_package)
    checks["has_music_package"] = bool(music_package)
    checks["has_camera_plan"] = bool(camera_plan)
    checks["has_director_notes"] = bool(director_notes)
    checks["manifest_tracks"] = bool(video_manifest.tracks)

    for key, ok in list(checks.items()):
        if not ok and key.startswith("has_") and key not in (
            "has_4k_or_higher",
        ):
            if key in ("has_voice_package", "has_music_package"):
                issues.append(
                    ValidationIssue(key, "warning", f"Check failed: {key}")
                )

    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]
    passed = len(errors) == 0 and checks.get("has_scenes") and checks.get("has_shots")
    score = 1.0
    score -= 0.15 * len(errors)
    score -= 0.05 * len(warnings)
    score = max(0.0, min(1.0, round(score, 3)))

    return ExportValidation(
        passed=passed,
        score=score,
        issues=issues,
        checks=checks,
    )
