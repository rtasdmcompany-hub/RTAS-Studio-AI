"""Workflow authorization, secure execution guards, audit logs."""

from __future__ import annotations

from typing import Any

from app.services.workflow_pipeline import store
from app.services.workflow_pipeline.models import AuditEntry, WorkflowJob, new_id


class WorkflowAuthError(PermissionError):
    pass


def assert_user(user_id: str | None) -> str:
    uid = (user_id or "").strip()
    if not uid:
        raise WorkflowAuthError("user_id required for workflow authorization")
    return uid


def authorize(user_id: str, job: WorkflowJob) -> None:
    if job.user_id != user_id:
        raise WorkflowAuthError("workflow access denied")


def secure_execution_guard(job: WorkflowJob) -> None:
    if job.status == "cancelled":
        raise WorkflowAuthError("cannot execute cancelled workflow")
    if not job.prompt or not job.prompt.strip():
        raise WorkflowAuthError("secure execution blocked: empty prompt")


def audit(user_id: str, action: str, workflow_id: str, detail: str = "") -> dict[str, Any]:
    entry = AuditEntry(
        audit_id=new_id("audit"),
        user_id=user_id,
        action=action,
        workflow_id=workflow_id,
        detail=detail,
    )
    store.add_audit(entry)
    return entry.to_dict()
