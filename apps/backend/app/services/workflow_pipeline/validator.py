"""Pipeline Validator — structure, deps, and runtime checks."""

from __future__ import annotations

from typing import Any

from app.services.workflow_pipeline.dependencies import resolve_order
from app.services.workflow_pipeline.models import PRODUCTION_STAGES, StageSpec, WorkflowJob


KNOWN_STAGES = frozenset(PRODUCTION_STAGES) | {
    "prompt",
    "story",
    "director",
    "scene",
    "character",
    "motion",
    "camera",
    "environment",
    "audio",
    "video",
    "export",
    "download",
    "custom",
}


def validate_template_stages(stages: list[StageSpec]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    names = [s.name for s in stages]
    if not names:
        errors.append("pipeline has no stages")
    if len(names) != len(set(names)):
        errors.append("duplicate stage names")
    name_set = set(names)
    for s in stages:
        if s.name not in KNOWN_STAGES and not s.name.startswith("custom_"):
            warnings.append(f"unknown stage '{s.name}' (allowed as custom)")
        for dep in s.depends_on:
            if dep not in name_set:
                errors.append(f"stage '{s.name}' depends on missing '{dep}'")
    order = resolve_order(stages)
    if len(order) != len(names) and not errors:
        errors.append("dependency cycle detected")
    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "order": order,
    }


def validate_workflow(job: WorkflowJob, specs: list[StageSpec]) -> dict[str, Any]:
    base = validate_template_stages(specs)
    if job.status in ("running", "queued") and not job.prompt.strip():
        base["errors"].append("prompt required for execution")
        base["valid"] = False
    if not job.user_id:
        base["errors"].append("user_id required")
        base["valid"] = False
    return base


def validate_stage_output(stage_name: str, output: dict[str, Any] | None) -> bool:
    if not output:
        return False
    return bool(output.get("ok")) and output.get("stage") == stage_name
