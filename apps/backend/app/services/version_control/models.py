"""Domain models for version control, approval & review."""

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
class ProjectVersion:
    id: str
    organization_id: str
    project_id: str
    version_number: int
    created_by_id: str
    workspace_id: str | None = None
    label: str | None = None
    notes: str | None = None
    status: str = "draft"
    parent_version_id: str | None = None
    is_current: bool = False
    snapshot: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "projectId": self.project_id,
            "versionNumber": self.version_number,
            "label": self.label,
            "notes": self.notes,
            "status": self.status,
            "createdById": self.created_by_id,
            "parentVersionId": self.parent_version_id,
            "isCurrent": self.is_current,
            "snapshot": dict(self.snapshot),
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class VersionSnapshot:
    id: str
    version_id: str
    payload: dict[str, Any]
    name: str | None = None
    checksum: str | None = None
    size_bytes: int = 0
    created_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "versionId": self.version_id,
            "name": self.name,
            "payload": dict(self.payload),
            "checksum": self.checksum,
            "sizeBytes": self.size_bytes,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class ApprovalRequest:
    id: str
    organization_id: str
    project_id: str
    requested_by_id: str
    workspace_id: str | None = None
    version_id: str | None = None
    reviewer_id: str | None = None
    status: str = "pending_review"
    scope: str = "internal"
    title: str | None = None
    notes: str | None = None
    decided_at: datetime | None = None
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "projectId": self.project_id,
            "versionId": self.version_id,
            "requestedById": self.requested_by_id,
            "reviewerId": self.reviewer_id,
            "status": self.status,
            "scope": self.scope,
            "title": self.title,
            "notes": self.notes,
            "decidedAt": _iso(self.decided_at),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class ApprovalHistoryEntry:
    id: str
    approval_id: str
    actor_id: str
    to_status: str
    from_status: str | None = None
    note: str | None = None
    created_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "approvalId": self.approval_id,
            "actorId": self.actor_id,
            "fromStatus": self.from_status,
            "toStatus": self.to_status,
            "note": self.note,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class Review:
    id: str
    organization_id: str
    project_id: str
    created_by_id: str
    workspace_id: str | None = None
    version_id: str | None = None
    approval_id: str | None = None
    assignee_id: str | None = None
    review_type: str = "internal"
    status: str = "pending_review"
    summary: str | None = None
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "projectId": self.project_id,
            "versionId": self.version_id,
            "approvalId": self.approval_id,
            "createdById": self.created_by_id,
            "assigneeId": self.assignee_id,
            "reviewType": self.review_type,
            "status": self.status,
            "summary": self.summary,
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class ReviewComment:
    id: str
    review_id: str
    author_id: str
    body: str
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "reviewId": self.review_id,
            "authorId": self.author_id,
            "body": self.body,
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class ChangeLogEntry:
    id: str
    organization_id: str
    project_id: str
    change_type: str
    summary: str
    workspace_id: str | None = None
    actor_id: str | None = None
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    version_id: str | None = None
    created_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "projectId": self.project_id,
            "actorId": self.actor_id,
            "changeType": self.change_type,
            "summary": self.summary,
            "before": dict(self.before) if self.before else None,
            "after": dict(self.after) if self.after else None,
            "metadata": dict(self.metadata),
            "versionId": self.version_id,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class RollbackRecord:
    id: str
    organization_id: str
    project_id: str
    to_version_id: str
    actor_id: str
    workspace_id: str | None = None
    from_version_id: str | None = None
    note: str | None = None
    created_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "projectId": self.project_id,
            "fromVersionId": self.from_version_id,
            "toVersionId": self.to_version_id,
            "actorId": self.actor_id,
            "note": self.note,
            "createdAt": _iso(self.created_at),
        }
