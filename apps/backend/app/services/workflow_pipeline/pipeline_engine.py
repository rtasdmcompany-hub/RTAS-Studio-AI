"""Pipeline Engine — execute stages with validation and retries."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from app.services.workflow_pipeline import automation, store
from app.services.workflow_pipeline.dependencies import next_ready_stages, stage_map
from app.services.workflow_pipeline.models import StageSpec, WorkflowJob
from app.services.workflow_pipeline.validator import validate_stage_output
from app.services.workflow_pipeline.version import DEFAULT_MAX_RETRIES


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def execute_stage(
    job: WorkflowJob,
    stage_name: str,
    *,
    work_ms: float = 2.0,
    force_fail: bool = False,
) -> dict[str, Any]:
    """Simulate secure stage execution for the production chain."""
    runtime = stage_map(job)[stage_name]
    runtime.status = "running"
    runtime.started_at = _now()
    job.active_stage = stage_name
    job.status = "running"
    store.save(job)
    automation.log_action(job.workflow_id, "stage_start", f"running {stage_name}", stage=stage_name)

    t0 = time.perf_counter()
    # Deterministic tiny sleep for realism in tests (overridable via metadata)
    delay = float(job.metadata.get("work_ms", work_ms)) / 1000.0
    if delay > 0:
        time.sleep(min(delay, 0.05))

    fail_stages = set(job.metadata.get("fail_stages") or [])
    permanent = set(job.metadata.get("permanent_fail_stages") or [])
    fail_until = int(job.metadata.get("fail_until_retry", 1))
    should_fail = force_fail or stage_name in permanent or (
        stage_name in fail_stages and runtime.retry_count < fail_until
    )
    if should_fail:
        elapsed = (time.perf_counter() - t0) * 1000.0
        runtime.processing_time_ms = elapsed
        runtime.status = "failed"
        runtime.error = f"stage {stage_name} failed"
        runtime.completed_at = _now()
        runtime.logs.append(runtime.error)
        store.save(job)
        automation.log_action(
            job.workflow_id, "stage_fail", runtime.error, stage=stage_name
        )
        return {"ok": False, "stage": stage_name, "error": runtime.error}

    output = {
        "ok": True,
        "stage": stage_name,
        "summary": f"{stage_name} produced for prompt",
        "prompt_echo": job.prompt[:120],
        "project_id": job.project_id,
    }
    if not validate_stage_output(stage_name, output):
        runtime.status = "failed"
        runtime.error = "validation failed"
        runtime.completed_at = _now()
        store.save(job)
        return {"ok": False, "stage": stage_name, "error": runtime.error}

    elapsed = (time.perf_counter() - t0) * 1000.0
    runtime.processing_time_ms = elapsed
    runtime.output = output
    runtime.status = "completed"
    runtime.completed_at = _now()
    runtime.error = None
    runtime.logs.append(f"completed in {elapsed:.1f}ms")
    store.save(job)
    automation.log_action(
        job.workflow_id, "stage_complete", f"{stage_name} ok", stage=stage_name
    )
    automation.log_action(
        job.workflow_id, "validate", f"auto validation passed for {stage_name}", stage=stage_name
    )
    return output


def advance_pipeline(job: WorkflowJob, specs: list[StageSpec]) -> str:
    """
    Run next ready stages until blocked, complete, or failed.
    Returns terminal-ish status string for the workflow.
    """
    spec_map = {s.name: s for s in specs}
    max_loops = len(job.stages) * (DEFAULT_MAX_RETRIES + 2)
    loops = 0

    while loops < max_loops:
        loops += 1
        if job.status == "cancelled":
            return "cancelled"

        ready = next_ready_stages(job, spec_map)
        if not ready:
            # All done or blocked
            if all(s.status == "completed" or s.status == "skipped" for s in job.stages):
                return "completed"
            if any(s.status == "failed" for s in job.stages):
                # Try auto retry on failed stages
                retried = False
                for s in job.stages:
                    if s.status != "failed":
                        continue
                    spec = spec_map[s.name]
                    if automation.should_auto_retry(s.retry_count, spec.max_retries):
                        s.retry_count += 1
                        s.status = "retrying"
                        job.retry_count += 1
                        job.status = "recovering"
                        automation.log_action(
                            job.workflow_id,
                            "retry",
                            f"auto retry {s.name} attempt {s.retry_count}",
                            stage=s.name,
                        )
                        retried = True
                if retried:
                    store.save(job)
                    continue
                return "failed"
            # waiting on deps
            job.status = "waiting"
            store.save(job)
            return "waiting"

        for name in ready:
            if job.status == "cancelled":
                return "cancelled"
            stage = stage_map(job)[name]
            if stage.status == "retrying":
                automation.log_action(
                    job.workflow_id, "resume", f"resuming stage {name}", stage=name
                )
            result = execute_stage(job, name)
            if not result.get("ok"):
                # immediate retry loop handled above on next pass
                break

    if all(s.status == "completed" or s.status == "skipped" for s in job.stages):
        return "completed"
    if any(s.status == "failed" for s in job.stages):
        return "failed"
    return job.status
