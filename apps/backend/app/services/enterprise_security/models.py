"""Datamodels for security, compliance, and audit."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

Role = Literal["admin", "team", "user", "service"]
AuthMethod = Literal["jwt", "session", "api_key", "service_account"]
AuditAction = Literal[
    "login",
    "logout",
    "api_call",
    "job_creation",
    "job_cancellation",
    "ai_provider_usage",
    "prompt_submission",
    "export_request",
    "download",
    "admin_action",
    "security_violation",
    "unauthorized",
    "validate",
]
EventSeverity = Literal["info", "low", "medium", "high", "critical"]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


@dataclass
class Principal:
    principal_id: str
    role: Role
    auth_method: AuthMethod
    subject: str
    scopes: list[str] = field(default_factory=list)
    team_id: str | None = None
    expires_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AuditLogEntry:
    audit_id: str
    action: AuditAction
    actor_id: str
    role: Role | str
    resource: str
    detail: str = ""
    ip: str | None = None
    success: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SecurityEvent:
    event_id: str
    event_type: str
    severity: EventSeverity
    actor_id: str | None
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AccessLogEntry:
    access_id: str
    actor_id: str
    method: str
    path: str
    status: int
    authorized: bool
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SecurityPolicy:
    policy_id: str
    name: str
    enabled: bool = True
    rules: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ComplianceReport:
    report_id: str
    period: str
    retention_days: int
    consent_count: int
    audit_count: int
    privacy_controls: dict[str, Any]
    findings: list[str]
    healthy: bool
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
