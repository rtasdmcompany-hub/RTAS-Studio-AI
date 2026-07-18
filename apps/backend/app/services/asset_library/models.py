"""Domain models for asset library."""

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
class LibraryAsset:
    id: str
    organization_id: str
    owner_id: str
    name: str
    slug: str
    asset_type: str
    storage_key: str
    workspace_id: str | None = None
    mime_type: str | None = None
    category: str = "general"
    status: str = "active"
    storage_url: str | None = None
    size_bytes: int = 0
    checksum: str | None = None
    current_version: int = 1
    is_favorite: bool = False
    is_shared: bool = False
    download_count: int = 0
    use_count: int = 0
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    preview_url: str | None = None
    content_ref: str | None = None  # in-memory / URL reference
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
            "assetType": self.asset_type,
            "mimeType": self.mime_type,
            "category": self.category,
            "status": self.status,
            "storageKey": self.storage_key,
            "storageUrl": self.storage_url,
            "sizeBytes": self.size_bytes,
            "checksum": self.checksum,
            "currentVersion": self.current_version,
            "isFavorite": self.is_favorite,
            "isShared": self.is_shared,
            "downloadCount": self.download_count,
            "useCount": self.use_count,
            "tags": list(self.tags),
            "metadata": dict(self.metadata),
            "previewUrl": self.preview_url,
            "archivedAt": _iso(self.archived_at),
            "deletedAt": _iso(self.deleted_at),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class AssetVersion:
    id: str
    asset_id: str
    version: int
    storage_key: str
    created_by_id: str
    storage_url: str | None = None
    size_bytes: int = 0
    checksum: str | None = None
    note: str | None = None
    content_ref: str | None = None
    created_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "assetId": self.asset_id,
            "version": self.version,
            "storageKey": self.storage_key,
            "storageUrl": self.storage_url,
            "sizeBytes": self.size_bytes,
            "checksum": self.checksum,
            "note": self.note,
            "createdById": self.created_by_id,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class AssetPermission:
    id: str
    asset_id: str
    subject_type: str  # user | team | workspace | organization
    subject_id: str
    role: str = "read"
    created_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "assetId": self.asset_id,
            "subjectType": self.subject_type,
            "subjectId": self.subject_id,
            "role": self.role,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class AssetActivity:
    id: str
    asset_id: str
    actor_id: str
    action: str
    detail: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "assetId": self.asset_id,
            "actorId": self.actor_id,
            "action": self.action,
            "detail": self.detail,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
        }


@dataclass
class AssetCollection:
    id: str
    organization_id: str
    name: str
    slug: str
    workspace_id: str | None = None
    library_scope: str = "organization"
    description: str | None = None
    asset_ids: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "name": self.name,
            "slug": self.slug,
            "libraryScope": self.library_scope,
            "description": self.description,
            "assetIds": list(self.asset_ids),
            "createdAt": _iso(self.created_at),
        }
