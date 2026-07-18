"""Domain models for multi-tenant SaaS foundation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
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


@dataclass
class Permission:
    id: str
    key: str
    name: str
    description: str | None = None
    category: str = "general"
    created_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class Role:
    id: str
    key: str
    name: str
    description: str | None = None
    organization_id: str | None = None
    is_system: bool = True
    rank: int = 0
    permission_keys: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "organizationId": self.organization_id,
            "isSystem": self.is_system,
            "rank": self.rank,
            "permissions": list(self.permission_keys),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class Organization:
    id: str
    name: str
    slug: str
    owner_id: str
    plan: str = "free"
    status: str = "active"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "ownerId": self.owner_id,
            "plan": self.plan,
            "status": self.status,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class Workspace:
    id: str
    organization_id: str
    name: str
    slug: str
    status: str = "active"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "name": self.name,
            "slug": self.slug,
            "status": self.status,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class Team:
    id: str
    organization_id: str
    name: str
    slug: str
    workspace_id: str | None = None
    status: str = "active"
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "name": self.name,
            "slug": self.slug,
            "status": self.status,
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class Member:
    id: str
    organization_id: str
    user_id: str
    role_id: str
    role_key: str
    workspace_id: str | None = None
    status: str = "active"
    joined_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "userId": self.user_id,
            "roleId": self.role_id,
            "roleKey": self.role_key,
            "status": self.status,
            "joinedAt": _iso(self.joined_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class TeamMember:
    id: str
    team_id: str
    user_id: str
    status: str = "active"
    team_role: str = "member"
    joined_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "teamId": self.team_id,
            "userId": self.user_id,
            "teamRole": self.team_role,
            "status": self.status,
            "joinedAt": _iso(self.joined_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class Invite:
    id: str
    organization_id: str
    email: str
    role_id: str
    role_key: str
    token: str
    invited_by_id: str
    expires_at: datetime
    workspace_id: str | None = None
    status: str = "pending"
    accepted_at: datetime | None = None
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "email": self.email,
            "roleId": self.role_id,
            "roleKey": self.role_key,
            "token": self.token,
            "status": self.status,
            "invitedById": self.invited_by_id,
            "expiresAt": _iso(self.expires_at),
            "acceptedAt": _iso(self.accepted_at),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


def model_as_dict(obj: Any) -> dict[str, Any]:
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    return asdict(obj)
