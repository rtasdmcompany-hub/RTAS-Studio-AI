"""Domain models for enterprise automation & event-driven platform."""

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
class AutomationRuleRecord:
    id: str
    organization_id: str
    workspace_id: str | None
    owner_user_id: str
    name: str
    slug: str
    mode: str = "event"
    status: str = "active"
    description: str = ""
    trigger_event: str = ""
    conditions: dict[str, Any] = field(default_factory=dict)
    actions: list[dict[str, Any]] = field(default_factory=list)
    integration_id: str | None = None
    priority: int = 100
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
            "mode": self.mode,
            "status": self.status,
            "description": self.description,
            "triggerEvent": self.trigger_event,
            "conditions": dict(self.conditions),
            "actions": list(self.actions),
            "integrationId": self.integration_id,
            "priority": self.priority,
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class AutomationExecutionRecord:
    id: str
    organization_id: str
    workspace_id: str | None
    rule_id: str
    event_id: str | None
    status: str = "queued"
    trigger: str = "event"
    results: list[dict[str, Any]] = field(default_factory=list)
    error: str = ""
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "ruleId": self.rule_id,
            "eventId": self.event_id,
            "status": self.status,
            "trigger": self.trigger,
            "results": list(self.results),
            "error": self.error,
            "startedAt": _iso(self.started_at),
            "completedAt": _iso(self.completed_at),
            "createdAt": _iso(self.created_at),
        }


@dataclass
class EventBusRecord:
    id: str
    organization_id: str
    workspace_id: str | None
    event_type: str
    category: str
    payload: dict[str, Any] = field(default_factory=dict)
    actor_user_id: str = ""
    signature: str = ""
    status: str = "published"
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "eventType": self.event_type,
            "category": self.category,
            "payload": dict(self.payload),
            "actorUserId": self.actor_user_id,
            "signature": self.signature,
            "status": self.status,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class EventLogRecord:
    id: str
    event_id: str
    organization_id: str
    action: str
    message: str = ""
    success: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "eventId": self.event_id,
            "organizationId": self.organization_id,
            "action": self.action,
            "message": self.message,
            "success": self.success,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
        }


@dataclass
class EventSubscriptionRecord:
    id: str
    organization_id: str
    workspace_id: str | None
    event_type: str
    rule_id: str | None
    target: str = "automation"
    status: str = "active"
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "eventType": self.event_type,
            "ruleId": self.rule_id,
            "target": self.target,
            "status": self.status,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class IntegrationConnectionRecord:
    id: str
    organization_id: str
    workspace_id: str | None
    provider: str
    status: str = "connected"
    display_name: str = ""
    credentials_ref: str = ""
    webhook_secret: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    connected_by: str = ""
    connected_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "provider": self.provider,
            "status": self.status,
            "displayName": self.display_name,
            "metadata": dict(self.metadata),
            "connectedBy": self.connected_by,
            "connectedAt": _iso(self.connected_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class ScheduledAutomationRecord:
    id: str
    organization_id: str
    workspace_id: str | None
    rule_id: str
    kind: str = "once"
    cron: str = ""
    status: str = "scheduled"
    next_run_at: datetime | None = None
    last_run_at: datetime | None = None
    created_by: str = ""
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "ruleId": self.rule_id,
            "kind": self.kind,
            "cron": self.cron,
            "status": self.status,
            "nextRunAt": _iso(self.next_run_at),
            "lastRunAt": _iso(self.last_run_at),
            "createdBy": self.created_by,
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class AutomationHistoryRecord:
    id: str
    organization_id: str
    rule_id: str
    execution_id: str | None
    event_type: str
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "ruleId": self.rule_id,
            "executionId": self.execution_id,
            "eventType": self.event_type,
            "message": self.message,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
        }
