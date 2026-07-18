"""Domain models for platform administration & operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def new_id(prefix: str = "") -> str:
    return f"{prefix}{uuid4()}" if prefix else str(uuid4())


@dataclass
class PlatformSetting:
    id: str
    key: str
    category: str = "general"
    value: Any = None
    is_secret: bool = False
    description: str | None = None
    updated_by_id: str | None = None
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def to_dict(self, *, reveal_secrets: bool = False) -> dict[str, Any]:
        value = self.value
        if self.is_secret and not reveal_secrets and value is not None:
            value = "***"
        return {
            "id": self.id,
            "key": self.key,
            "category": self.category,
            "value": value,
            "isSecret": self.is_secret,
            "description": self.description,
            "updatedById": self.updated_by_id,
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class SystemConfiguration:
    id: str
    namespace: str
    config: dict[str, Any] = field(default_factory=dict)
    environment: str = "production"
    is_valid: bool = True
    validated_at: datetime | None = None
    validation_msg: str | None = None
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "namespace": self.namespace,
            "config": dict(self.config),
            "environment": self.environment,
            "isValid": self.is_valid,
            "validatedAt": _iso(self.validated_at),
            "validationMsg": self.validation_msg,
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class FeatureFlag:
    id: str
    key: str
    enabled: bool = False
    description: str | None = None
    rollout_percent: int = 100
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "key": self.key,
            "enabled": self.enabled,
            "description": self.description,
            "rolloutPercent": self.rollout_percent,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class MaintenanceEvent:
    id: str
    message: str
    status: str = "scheduled"
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    created_by_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status,
            "message": self.message,
            "startsAt": _iso(self.starts_at),
            "endsAt": _iso(self.ends_at),
            "createdById": self.created_by_id,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class AdminActivity:
    id: str
    actor_id: str
    action: str
    detail: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "actorId": self.actor_id,
            "action": self.action,
            "detail": self.detail,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
        }


@dataclass
class SystemLog:
    id: str
    source: str
    message: str
    level: str = "info"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "level": self.level,
            "source": self.source,
            "message": self.message,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
        }


@dataclass
class ScheduledTask:
    id: str
    name: str
    cron_expr: str | None = None
    status: str = "idle"
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None
    updated_by_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "cronExpr": self.cron_expr,
            "status": self.status,
            "lastRunAt": _iso(self.last_run_at),
            "nextRunAt": _iso(self.next_run_at),
            "updatedById": self.updated_by_id,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class OperationsHistory:
    id: str
    operation: str
    status: str = "success"
    actor_id: str | None = None
    detail: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "operation": self.operation,
            "status": self.status,
            "actorId": self.actor_id,
            "detail": self.detail,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
        }
