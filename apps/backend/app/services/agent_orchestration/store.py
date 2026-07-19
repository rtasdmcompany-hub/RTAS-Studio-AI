"""Thread-safe in-memory store for AI agents & workflow orchestration."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from app.services.agent_orchestration.models import (
        AgentEventRecord,
        AgentMemoryRecord,
        AgentWorkflowRecord,
        AIAgentRecord,
        ExecutionHistoryRecord,
        ScheduledJobRecord,
        WorkflowExecutionRecord,
        WorkflowTemplateRecord,
    )

_lock = threading.RLock()

_agents: OrderedDict[str, "AIAgentRecord"] = OrderedDict()
_workflows: OrderedDict[str, "AgentWorkflowRecord"] = OrderedDict()
_templates: OrderedDict[str, "WorkflowTemplateRecord"] = OrderedDict()
_executions: OrderedDict[str, "WorkflowExecutionRecord"] = OrderedDict()
_memory: OrderedDict[str, "AgentMemoryRecord"] = OrderedDict()
_memory_keys: dict[tuple[str, str], str] = {}
_jobs: OrderedDict[str, "ScheduledJobRecord"] = OrderedDict()
_history: OrderedDict[str, "ExecutionHistoryRecord"] = OrderedDict()
_events: OrderedDict[str, "AgentEventRecord"] = OrderedDict()
_queue: list[str] = []

_op_timings: list[float] = []
_op_count = 0
_error_count = 0


def reset_store() -> None:
    global _op_count, _error_count
    with _lock:
        for coll in (
            _agents, _workflows, _templates, _executions, _memory,
            _memory_keys, _jobs, _history, _events, _queue,
        ):
            coll.clear()
        _op_timings.clear()
        _op_count = 0
        _error_count = 0


def record_error() -> None:
    global _error_count
    with _lock:
        _error_count += 1


@contextmanager
def timed_op() -> Iterator[None]:
    global _op_count
    start = time.perf_counter()
    try:
        yield
    except Exception:
        record_error()
        raise
    finally:
        ms = (time.perf_counter() - start) * 1000
        with _lock:
            _op_timings.append(ms)
            if len(_op_timings) > 500:
                del _op_timings[: len(_op_timings) - 500]
            _op_count += 1


def metrics() -> dict[str, Any]:
    with _lock:
        timings = list(_op_timings)
        avg = sum(timings) / len(timings) if timings else 0.0
        return {
            "opCount": _op_count,
            "errorCount": _error_count,
            "avgLatencyMs": round(avg, 3),
            "agents": len(_agents),
            "workflows": len(_workflows),
            "templates": len(_templates),
            "executions": len(_executions),
            "memoryEntries": len(_memory),
            "scheduledJobs": len(_jobs),
            "history": len(_history),
            "agentEvents": len(_events),
            "queueDepth": len(_queue),
        }


def save_agent(agent: "AIAgentRecord") -> None:
    with _lock:
        _agents[agent.id] = agent


def get_agent(agent_id: str) -> "AIAgentRecord | None":
    with _lock:
        return _agents.get(agent_id)


def list_agents(
    *,
    organization_id: str | None = None,
    workspace_id: str | None = None,
    agent_type: str | None = None,
    status: str | None = None,
) -> list["AIAgentRecord"]:
    with _lock:
        return [
            a
            for a in _agents.values()
            if (organization_id is None or a.organization_id == organization_id)
            and (workspace_id is None or a.workspace_id == workspace_id)
            and (agent_type is None or a.agent_type == agent_type)
            and (status is None or a.status == status)
            and a.status != "archived"
        ]


def save_workflow(workflow: "AgentWorkflowRecord") -> None:
    with _lock:
        _workflows[workflow.id] = workflow


def get_workflow(workflow_id: str) -> "AgentWorkflowRecord | None":
    with _lock:
        return _workflows.get(workflow_id)


def list_workflows(
    *, organization_id: str | None = None, workspace_id: str | None = None
) -> list["AgentWorkflowRecord"]:
    with _lock:
        return [
            w
            for w in _workflows.values()
            if (organization_id is None or w.organization_id == organization_id)
            and (workspace_id is None or w.workspace_id == workspace_id)
            and w.status != "archived"
        ]


def save_template(template: "WorkflowTemplateRecord") -> None:
    with _lock:
        _templates[template.id] = template


def get_template_by_slug(slug: str) -> "WorkflowTemplateRecord | None":
    with _lock:
        for t in _templates.values():
            if t.slug == slug:
                return t
        return None


def list_templates() -> list["WorkflowTemplateRecord"]:
    with _lock:
        return list(_templates.values())


def save_execution(execution: "WorkflowExecutionRecord") -> None:
    with _lock:
        _executions[execution.id] = execution


def get_execution(execution_id: str) -> "WorkflowExecutionRecord | None":
    with _lock:
        return _executions.get(execution_id)


def list_executions(
    *,
    organization_id: str | None = None,
    workflow_id: str | None = None,
    limit: int = 100,
) -> list["WorkflowExecutionRecord"]:
    with _lock:
        items = [
            e
            for e in _executions.values()
            if (organization_id is None or e.organization_id == organization_id)
            and (workflow_id is None or e.workflow_id == workflow_id)
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


def enqueue(execution_id: str, *, priority: str = "normal") -> None:
    with _lock:
        if priority in ("high", "critical"):
            _queue.insert(0, execution_id)
        else:
            _queue.append(execution_id)


def dequeue() -> str | None:
    with _lock:
        if not _queue:
            return None
        return _queue.pop(0)


def queue_depth() -> int:
    with _lock:
        return len(_queue)


def save_memory(record: "AgentMemoryRecord") -> None:
    with _lock:
        _memory[record.id] = record
        _memory_keys[(record.agent_id, record.key)] = record.id


def get_memory(agent_id: str, key: str) -> "AgentMemoryRecord | None":
    with _lock:
        mid = _memory_keys.get((agent_id, key))
        return _memory.get(mid) if mid else None


def list_memory(agent_id: str, *, limit: int = 100) -> list["AgentMemoryRecord"]:
    with _lock:
        items = [m for m in _memory.values() if m.agent_id == agent_id]
        items.sort(key=lambda x: x.updated_at, reverse=True)
        return items[:limit]


def count_memory(agent_id: str) -> int:
    with _lock:
        return sum(1 for m in _memory.values() if m.agent_id == agent_id)


def delete_memory(memory_id: str) -> None:
    with _lock:
        record = _memory.pop(memory_id, None)
        if record is None:
            return
        key = (record.agent_id, record.key)
        if _memory_keys.get(key) == memory_id:
            _memory_keys.pop(key, None)


def save_job(job: "ScheduledJobRecord") -> None:
    with _lock:
        _jobs[job.id] = job


def get_job(job_id: str) -> "ScheduledJobRecord | None":
    with _lock:
        return _jobs.get(job_id)


def list_jobs(
    *, organization_id: str | None = None, status: str | None = None
) -> list["ScheduledJobRecord"]:
    with _lock:
        return [
            j
            for j in _jobs.values()
            if (organization_id is None or j.organization_id == organization_id)
            and (status is None or j.status == status)
        ]


def save_history(record: "ExecutionHistoryRecord") -> None:
    with _lock:
        _history[record.id] = record
        if len(_history) > 100_000:
            _history.popitem(last=False)


def list_history(
    *,
    organization_id: str | None = None,
    execution_id: str | None = None,
    limit: int = 100,
) -> list["ExecutionHistoryRecord"]:
    with _lock:
        items = [
            h
            for h in _history.values()
            if (organization_id is None or h.organization_id == organization_id)
            and (execution_id is None or h.execution_id == execution_id)
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


def save_event(event: "AgentEventRecord") -> None:
    with _lock:
        _events[event.id] = event
        if len(_events) > 100_000:
            _events.popitem(last=False)


def list_events(
    *, organization_id: str | None = None, agent_id: str | None = None, limit: int = 100
) -> list["AgentEventRecord"]:
    with _lock:
        items = [
            e
            for e in _events.values()
            if (organization_id is None or e.organization_id == organization_id)
            and (agent_id is None or e.agent_id == agent_id)
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]
