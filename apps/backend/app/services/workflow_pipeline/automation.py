"""Automation Manager — trigger, retry, resume, recovery, cleanup, notifications."""

from __future__ import annotations

from typing import Any

from app.services.workflow_pipeline import store
from app.services.workflow_pipeline.models import AutomationLog, WorkflowJob, new_id


def log_action(
    workflow_id: str,
    action: str,
    detail: str,
    *,
    stage: str | None = None,
) -> dict[str, Any]:
    entry = AutomationLog(
        log_id=new_id("alog"),
        workflow_id=workflow_id,
        action=action,
        detail=detail,
        stage=stage,
    )
    store.add_automation_log(entry)
    job = store.get(workflow_id)
    if job:
        job.logs.append(f"[{action}] {detail}")
        job.logs = job.logs[-200:]
        if action == "notify":
            job.notifications.append(detail)
            job.notifications = job.notifications[-50:]
        store.save(job)
    return entry.to_dict()


def notify(job: WorkflowJob, message: str) -> None:
    log_action(job.workflow_id, "notify", message)


def auto_cleanup(job: WorkflowJob) -> None:
    """Trim bulky stage outputs after completion while keeping summary."""
    for s in job.stages:
        if s.status == "completed" and s.output:
            s.output = {
                "ok": s.output.get("ok", True),
                "stage": s.name,
                "summary": s.output.get("summary") or f"{s.name} complete",
            }
    job.logs = job.logs[-100:]
    store.save(job)
    log_action(job.workflow_id, "cleanup", "trimmed stage outputs and logs")


def should_auto_retry(stage_retry: int, max_retries: int) -> bool:
    return stage_retry < max_retries
