"""Domain models for AI agents, workflows, memory, schedules, and events."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def new_id(prefix: str = "") -> str:
    return f"{prefix}{uuid4()}"


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class AIAgentRecord:
    id: str
    organization_id: str
    workspace_id: str | None
    owner_user_id: str
    name: str
    slug: str
    agent_type: str
    description: str = ""
    status: str = "active"
    capabilities: list[str] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "ownerUserId": self.owner_user_id,
            "name": self.name,
            "slug": self.slug,
            "agentType": self.agent_type,
            "description": self.description,
            "status": self.status,
            "capabilities": list(self.capabilities),
            "config": dict(self.config),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class AgentWorkflowRecord:
    id: str
    organization_id: str
    workspace_id: str | None
    owner_user_id: str
    name: str
    slug: str
    description: str = ""
    trigger: str = "manual"
    mode: str = "sequential"
    status: str = "active"
    steps: list[dict[str, Any]] = field(default_factory=list)
    conditions: dict[str, Any] = field(default_factory=dict)
    template_id: str | None = None
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "ownerUserId": self.owner_user_id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "trigger": self.trigger,
            "mode": self.mode,
            "status": self.status,
            "steps": list(self.steps),
            "conditions": dict(self.conditions),
            "templateId": self.template_id,
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class WorkflowTemplateRecord:
    id: str
    slug: str
    name: str
    description: str = ""
    mode: str = "sequential"
    agent_types: list[str] = field(default_factory=list)
    steps: list[dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "slug": self.slug,
            "name": self.name,
            "description": self.description,
            "mode": self.mode,
            "agentTypes": list(self.agent_types),
            "steps": list(self.steps),
            "createdAt": _iso(self.created_at),
        }


@dataclass
class WorkflowExecutionRecord:
    id: str
    organization_id: str
    workspace_id: str | None
    workflow_id: str
    status: str = "queued"
    trigger: str = "manual"
    started_by: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    results: list[dict[str, Any]] = field(default_factory=list)
    error: str = ""
    retries: int = 0
    max_retries: int = 3
    priority: str = "normal"
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "workflowId": self.workflow_id,
            "status": self.status,
            "trigger": self.trigger,
            "startedBy": self.started_by,
            "context": dict(self.context),
            "results": list(self.results),
            "error": self.error,
            "retries": self.retries,
            "maxRetries": self.max_retries,
            "priority": self.priority,
            "startedAt": _iso(self.started_at),
            "completedAt": _iso(self.completed_at),
            "createdAt": _iso(self.created_at),
        }


@dataclass
class AgentMemoryRecord:
    id: str
    organization_id: str
    agent_id: str
    workspace_id: str | None
    key: str
    value: dict[str, Any] = field(default_factory=dict)
    execution_id: str | None = None
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "agentId": self.agent_id,
            "workspaceId": self.workspace_id,
            "key": self.key,
            "value": dict(self.value),
            "executionId": self.execution_id,
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class ScheduledJobRecord:
    id: str
    organization_id: str
    workspace_id: str | None
    workflow_id: str
    kind: str = "once"
    cron: str = ""
    priority: str = "normal"
    status: str = "scheduled"
    next_run_at: datetime | None = None
    last_run_at: datetime | None = None
    max_retries: int = 3
    created_by: str = ""
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "workflowId": self.workflow_id,
            "kind": self.kind,
            "cron": self.cron,
            "priority": self.priority,
            "status": self.status,
            "nextRunAt": _iso(self.next_run_at),
            "lastRunAt": _iso(self.last_run_at),
            "maxRetries": self.max_retries,
            "createdBy": self.created_by,
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class ExecutionHistoryRecord:
    id: str
    organization_id: str
    execution_id: str
    workflow_id: str
    event_type: str
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "executionId": self.execution_id,
            "workflowId": self.workflow_id,
            "eventType": self.event_type,
            "message": self.message,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
        }


@dataclass
class AgentEventRecord:
    id: str
    organization_id: str
    agent_id: str
    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    actor_user_id: str = ""
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "agentId": self.agent_id,
            "eventType": self.event_type,
            "payload": dict(self.payload),
            "actorUserId": self.actor_user_id,
            "createdAt": _iso(self.created_at),
        }
