"""Models for organization settings, workspace settings, and activity logs."""

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
    uid = str(uuid4())
    return f"{prefix}{uid}" if prefix else uid


TEAM_ROLES = ("lead", "member", "contributor")
TEAM_ROLE_PERMISSIONS = {
    "lead": frozenset({"team.read", "team.update", "team.delete", "member.update", "content.write"}),
    "member": frozenset({"team.read", "content.read", "content.write"}),
    "contributor": frozenset({"team.read", "content.read"}),
}


@dataclass
class OrganizationSettings:
    id: str
    organization_id: str
    timezone: str = "UTC"
    locale: str = "en"
    allow_invites: bool = True
    default_role: str = "viewer"
    settings: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "timezone": self.timezone,
            "locale": self.locale,
            "allowInvites": self.allow_invites,
            "defaultRole": self.default_role,
            "settings": dict(self.settings),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class WorkspaceSettings:
    id: str
    workspace_id: str
    visibility: str = "private"
    default_model: str | None = None
    settings: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "workspaceId": self.workspace_id,
            "visibility": self.visibility,
            "defaultModel": self.default_model,
            "settings": dict(self.settings),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class ActivityLog:
    id: str
    organization_id: str
    actor_id: str
    action: str
    workspace_id: str | None = None
    team_id: str | None = None
    detail: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "teamId": self.team_id,
            "actorId": self.actor_id,
            "action": self.action,
            "detail": self.detail,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
        }
