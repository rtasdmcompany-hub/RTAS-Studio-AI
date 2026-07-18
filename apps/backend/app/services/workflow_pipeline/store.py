"""Thread-safe workflow / pipeline / automation store."""

from __future__ import annotations

import threading
from collections import OrderedDict
from typing import TYPE_CHECKING

from app.services.workflow_pipeline.version import MAX_WORKFLOWS

if TYPE_CHECKING:
    from app.services.workflow_pipeline.models import (
        AuditEntry,
        AutomationLog,
        WorkflowJob,
    )

_lock = threading.Lock()
_workflows: OrderedDict[str, "WorkflowJob"] = OrderedDict()
_history: list[str] = []
_automation_logs: list["AutomationLog"] = []
_audits: list["AuditEntry"] = []


def save(job: "WorkflowJob") -> "WorkflowJob":
    with _lock:
        _workflows[job.workflow_id] = job
        if job.workflow_id not in _history:
            _history.append(job.workflow_id)
        while len(_workflows) > MAX_WORKFLOWS:
            old_id, _ = _workflows.popitem(last=False)
            try:
                _history.remove(old_id)
            except ValueError:
                pass
        return job


def get(workflow_id: str) -> "WorkflowJob | None":
    with _lock:
        return _workflows.get(workflow_id)


def all_jobs() -> list["WorkflowJob"]:
    with _lock:
        return list(_workflows.values())


def history(limit: int = 50) -> list["WorkflowJob"]:
    with _lock:
        ids = list(_history[-max(1, min(1000, limit)) :])
        return [j for jid in reversed(ids) if (j := _workflows.get(jid))]


def add_automation_log(entry: "AutomationLog") -> None:
    with _lock:
        _automation_logs.append(entry)
        if len(_automation_logs) > 5000:
            del _automation_logs[:1000]


def automation_logs(workflow_id: str | None = None, limit: int = 50) -> list["AutomationLog"]:
    with _lock:
        items = [
            e
            for e in _automation_logs
            if not workflow_id or e.workflow_id == workflow_id
        ]
        return list(reversed(items[-max(1, min(500, limit)) :]))


def add_audit(entry: "AuditEntry") -> None:
    with _lock:
        _audits.append(entry)
        if len(_audits) > 5000:
            del _audits[:1000]


def audits(limit: int = 50) -> list["AuditEntry"]:
    with _lock:
        return list(reversed(_audits[-max(1, min(500, limit)) :]))


def clear() -> None:
    with _lock:
        _workflows.clear()
        _history.clear()
        _automation_logs.clear()
        _audits.clear()
