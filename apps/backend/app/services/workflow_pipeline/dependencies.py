"""Dependency Manager — resolve stage readiness and order."""

from __future__ import annotations

from app.services.workflow_pipeline.models import StageRuntime, StageSpec, WorkflowJob


def stage_map(job: WorkflowJob) -> dict[str, StageRuntime]:
    return {s.name: s for s in job.stages}


def specs_from_job(job: WorkflowJob, template_stages: list[StageSpec]) -> dict[str, StageSpec]:
    return {s.name: s for s in template_stages}


def dependencies_met(
    stage_name: str,
    job: WorkflowJob,
    specs: dict[str, StageSpec],
) -> bool:
    spec = specs.get(stage_name)
    if not spec:
        return False
    runtime = stage_map(job)
    for dep in spec.depends_on:
        dep_rt = runtime.get(dep)
        if not dep_rt or dep_rt.status != "completed":
            return False
    return True


def dependencies_failed(
    stage_name: str,
    job: WorkflowJob,
    specs: dict[str, StageSpec],
) -> bool:
    spec = specs.get(stage_name)
    if not spec:
        return True
    runtime = stage_map(job)
    for dep in spec.depends_on:
        dep_rt = runtime.get(dep)
        if dep_rt and dep_rt.status == "failed" and not (specs.get(dep) and specs[dep].optional):
            return True
    return False


def next_ready_stages(job: WorkflowJob, specs: dict[str, StageSpec]) -> list[str]:
    ready = []
    for s in job.stages:
        if s.status in ("pending", "ready", "retrying"):
            if dependencies_failed(s.name, job, specs):
                continue
            if dependencies_met(s.name, job, specs):
                ready.append(s.name)
    return ready


def resolve_order(specs: list[StageSpec]) -> list[str]:
    """Topological order for validation / display."""
    remaining = {s.name: set(s.depends_on) for s in specs}
    order: list[str] = []
    while remaining:
        ready = [n for n, deps in remaining.items() if not deps]
        if not ready:
            # cycle — fall back to declared order
            return [s.name for s in specs]
        ready.sort()
        for n in ready:
            order.append(n)
            del remaining[n]
            for deps in remaining.values():
                deps.discard(n)
    return order
