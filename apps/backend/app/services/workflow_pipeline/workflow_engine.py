"""Workflow Engine — create, start, resume, cancel, query."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from app.services.workflow_pipeline import (
    automation,
    observability,
    pipeline_engine,
    scheduler,
    security,
    store,
    templates,
    validator,
)
from app.services.workflow_pipeline.models import (
    StageRuntime,
    WorkflowJob,
    new_id,
)
from app.services.workflow_pipeline.version import DEFAULT_MAX_RETRIES


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _specs_for(job: WorkflowJob):
    tpl = templates.get_template(job.template_id)
    return tpl.stages


def create_workflow(
    *,
    user_id: str,
    prompt: str,
    project_id: str | None = None,
    name: str | None = None,
    template_id: str | None = None,
    custom_stages: list[str] | None = None,
    auto_trigger: bool = True,
    metadata: dict[str, Any] | None = None,
    max_retries: int | None = None,
) -> dict[str, Any]:
    uid = security.assert_user(user_id)
    text = (prompt or "").strip()
    if not text:
        raise ValueError("prompt is required")

    if custom_stages:
        tpl = templates.register_custom_template(
            name or "custom workflow", custom_stages
        )
        tid = tpl.template_id
        specs = tpl.stages
    else:
        tpl = templates.get_template(template_id)
        tid = tpl.template_id
        specs = tpl.stages

    validation = validator.validate_template_stages(specs)
    if not validation["valid"]:
        raise ValueError("; ".join(validation["errors"]))

    wid = new_id("wf")
    stages = [StageRuntime(name=s.name, status="pending") for s in specs]
    job = WorkflowJob(
        workflow_id=wid,
        user_id=uid,
        project_id=project_id,
        name=name or tpl.name,
        template_id=tid,
        status="draft",
        prompt=text,
        stages=stages,
        max_retries=int(max_retries or DEFAULT_MAX_RETRIES),
        auto_trigger=auto_trigger,
        metadata=dict(metadata or {}),
    )
    store.save(job)
    automation.log_action(wid, "create", f"workflow created template={tid}")
    security.audit(uid, "create", wid, detail=tid)

    if auto_trigger:
        automation.log_action(wid, "auto_trigger", "auto start armed")
        return start_workflow(user_id=uid, workflow_id=wid)

    return {"ok": True, **job.to_dict(), "validation": validation}


def _run_workflow(workflow_id: str) -> None:
    job = store.get(workflow_id)
    if not job or job.status == "cancelled":
        return
    try:
        security.secure_execution_guard(job)
    except security.WorkflowAuthError as exc:
        job.status = "failed"
        job.logs.append(str(exc))
        store.save(job)
        return

    job.status = "running"
    job.started_at = job.started_at or _now()
    job._t0 = time.perf_counter()
    store.save(job)
    automation.log_action(workflow_id, "start", "pipeline execution started")

    specs = _specs_for(job)
    # Keep advancing until terminal (handles retries internally)
    for _ in range(len(job.stages) * (job.max_retries + 3)):
        job = store.get(workflow_id)
        if not job or job.status == "cancelled":
            return
        result = pipeline_engine.advance_pipeline(job, specs)
        job = store.get(workflow_id) or job
        if result == "completed":
            job.status = "completed"
            job.active_stage = None
            job.completed_at = _now()
            job.processing_time_ms = (time.perf_counter() - (job._t0 or time.perf_counter())) * 1000.0
            automation.auto_cleanup(job)
            automation.notify(job, f"workflow {workflow_id} completed")
            store.save(job)
            automation.log_action(workflow_id, "complete", "pipeline finished")
            return
        if result == "failed":
            job.status = "failed"
            job.completed_at = _now()
            job.processing_time_ms = (time.perf_counter() - (job._t0 or time.perf_counter())) * 1000.0
            automation.notify(job, f"workflow {workflow_id} failed")
            store.save(job)
            automation.log_action(workflow_id, "failed", "pipeline failed")
            return
        if result == "cancelled":
            return
        if result == "waiting":
            # dependency resolution will unstick on next pump if needed
            automation.log_action(workflow_id, "dependency", "auto dependency wait")
            time.sleep(0.01)
            # if still waiting with no ready stages and no retries — break
            continue
    job = store.get(workflow_id)
    if job and job.status not in ("completed", "failed", "cancelled"):
        job.status = "failed"
        job.logs.append("pipeline exceeded advance loops")
        store.save(job)


def start_workflow(*, user_id: str, workflow_id: str) -> dict[str, Any]:
    uid = security.assert_user(user_id)
    job = store.get(workflow_id)
    if not job:
        raise ValueError("workflow not found")
    security.authorize(uid, job)
    if job.status in ("completed", "cancelled"):
        raise ValueError(f"cannot start workflow in status {job.status}")

    specs = _specs_for(job)
    validation = validator.validate_workflow(job, specs)
    if not validation["valid"]:
        raise ValueError("; ".join(validation["errors"]))

    # Reset failed stages for fresh start if draft/queued
    if job.status in ("draft", "failed", "paused"):
        for s in job.stages:
            if s.status in ("failed", "pending", "ready"):
                if job.status == "draft" or s.status != "completed":
                    if s.status != "completed":
                        s.status = "pending"
                        s.error = None

    job.status = "queued"
    store.save(job)
    security.audit(uid, "start", workflow_id)
    automation.log_action(workflow_id, "queue", "queued for scheduler")
    scheduler.enqueue(workflow_id)
    scheduler.pump(_run_workflow)
    # For tests / sync API: wait briefly for completion of short pipelines
    wait_ms = float(job.metadata.get("wait_ms", 5000))
    deadline = time.time() + (wait_ms / 1000.0)
    while time.time() < deadline:
        job = store.get(workflow_id)
        if job and job.status in ("completed", "failed", "cancelled"):
            break
        scheduler.pump(_run_workflow)
        time.sleep(0.02)
    job = store.get(workflow_id)
    return {"ok": True, **(job.to_dict() if job else {"workflow_id": workflow_id})}


def resume_workflow(*, user_id: str, workflow_id: str) -> dict[str, Any]:
    uid = security.assert_user(user_id)
    job = store.get(workflow_id)
    if not job:
        raise ValueError("workflow not found")
    security.authorize(uid, job)
    if job.status == "cancelled":
        raise ValueError("cannot resume cancelled workflow")
    if job.status == "completed":
        return {"ok": True, **job.to_dict()}

    # Mark failed stages as retrying for auto resume
    for s in job.stages:
        if s.status == "failed":
            s.status = "retrying"
            automation.log_action(
                workflow_id, "resume", f"auto resume stage {s.name}", stage=s.name
            )
    job.status = "queued"
    store.save(job)
    security.audit(uid, "resume", workflow_id)
    automation.log_action(workflow_id, "auto_resume", "workflow resumed")
    scheduler.enqueue(workflow_id)
    scheduler.pump(_run_workflow)
    wait_ms = float(job.metadata.get("wait_ms", 5000))
    deadline = time.time() + (wait_ms / 1000.0)
    while time.time() < deadline:
        job = store.get(workflow_id)
        if job and job.status in ("completed", "failed", "cancelled"):
            break
        scheduler.pump(_run_workflow)
        time.sleep(0.02)
    job = store.get(workflow_id)
    return {"ok": True, **(job.to_dict() if job else {"workflow_id": workflow_id})}


def cancel_workflow(*, user_id: str, workflow_id: str) -> dict[str, Any]:
    uid = security.assert_user(user_id)
    job = store.get(workflow_id)
    if not job:
        raise ValueError("workflow not found")
    security.authorize(uid, job)
    job.status = "cancelled"
    job.completed_at = _now()
    job.active_stage = None
    store.save(job)
    automation.notify(job, f"workflow {workflow_id} cancelled")
    automation.log_action(workflow_id, "cancel", "workflow cancelled")
    security.audit(uid, "cancel", workflow_id)
    return {"ok": True, **job.to_dict()}


def get_workflow(workflow_id: str, *, user_id: str | None = None) -> dict[str, Any]:
    job = store.get(workflow_id)
    if not job:
        raise ValueError("workflow not found")
    if user_id:
        security.authorize(security.assert_user(user_id), job)
    return {
        "ok": True,
        **job.to_dict(),
        "automation_logs": [e.to_dict() for e in store.automation_logs(workflow_id, limit=30)],
    }


def workflow_history(*, user_id: str | None = None, limit: int = 50) -> dict[str, Any]:
    jobs = store.history(limit=limit)
    if user_id:
        uid = security.assert_user(user_id)
        jobs = [j for j in jobs if j.user_id == uid]
    return {
        "ok": True,
        "count": len(jobs),
        "history": [j.to_dict() for j in jobs],
        "observability": observability.metrics(),
    }


def pipeline_status() -> dict[str, Any]:
    scheduler.pump(_run_workflow)
    return {"ok": True, **observability.pipeline_status_snapshot()}
