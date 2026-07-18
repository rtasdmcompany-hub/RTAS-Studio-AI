"""Domain models for project collaboration."""

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
class CollabProject:
    id: str
    organization_id: str
    owner_id: str
    name: str
    slug: str
    workspace_id: str | None = None
    description: str | None = None
    status: str = "draft"
    is_favorite: bool = False
    is_shared: bool = False
    template_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    archived_at: datetime | None = None
    deleted_at: datetime | None = None
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "ownerId": self.owner_id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "status": self.status,
            "isFavorite": self.is_favorite,
            "isShared": self.is_shared,
            "templateId": self.template_id,
            "metadata": dict(self.metadata),
            "archivedAt": _iso(self.archived_at),
            "deletedAt": _iso(self.deleted_at),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class ProjectMember:
    id: str
    project_id: str
    user_id: str
    role_key: str = "contributor"
    status: str = "active"
    joined_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "projectId": self.project_id,
            "userId": self.user_id,
            "roleKey": self.role_key,
            "status": self.status,
            "joinedAt": _iso(self.joined_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class ProjectActivity:
    id: str
    project_id: str
    actor_id: str
    action: str
    detail: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "projectId": self.project_id,
            "actorId": self.actor_id,
            "action": self.action,
            "detail": self.detail,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
        }


@dataclass
class ProjectTimelineEvent:
    id: str
    project_id: str
    actor_id: str
    event_type: str
    summary: str
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "projectId": self.project_id,
            "actorId": self.actor_id,
            "eventType": self.event_type,
            "summary": self.summary,
            "payload": dict(self.payload),
            "createdAt": _iso(self.created_at),
        }


@dataclass
class ProjectTemplate:
    id: str
    key: str
    name: str
    description: str | None = None
    organization_id: str | None = None
    default_status: str = "draft"
    blueprint: dict[str, Any] = field(default_factory=dict)
    is_system: bool = False
    created_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "organizationId": self.organization_id,
            "defaultStatus": self.default_status,
            "blueprint": dict(self.blueprint),
            "isSystem": self.is_system,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class ProjectSettings:
    id: str
    project_id: str
    visibility: str = "private"
    allow_comments: bool = True
    allow_tasks: bool = True
    settings: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "projectId": self.project_id,
            "visibility": self.visibility,
            "allowComments": self.allow_comments,
            "allowTasks": self.allow_tasks,
            "settings": dict(self.settings),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class CollaborationNote:
    id: str
    project_id: str
    author_id: str
    body: str
    is_internal: bool = True
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "projectId": self.project_id,
            "authorId": self.author_id,
            "body": self.body,
            "isInternal": self.is_internal,
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class ProjectTask:
    id: str
    project_id: str
    title: str
    created_by_id: str
    description: str | None = None
    status: str = "open"
    assignee_id: str | None = None
    due_at: datetime | None = None
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "projectId": self.project_id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "assigneeId": self.assignee_id,
            "createdById": self.created_by_id,
            "dueAt": _iso(self.due_at),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }
