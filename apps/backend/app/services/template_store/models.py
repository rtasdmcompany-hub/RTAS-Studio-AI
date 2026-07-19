"""Domain models for templates, versions, libraries, and the search index."""

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
class TemplateVersion:
    id: str
    template_id: str
    version: str
    changelog: str = ""
    asset_uri: str = ""
    checksum: str = ""
    created_by: str = ""
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "templateId": self.template_id,
            "version": self.version,
            "changelog": self.changelog,
            "assetUri": self.asset_uri,
            "checksum": self.checksum,
            "createdBy": self.created_by,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class Template:
    id: str
    organization_id: str
    owner_user_id: str
    name: str
    slug: str
    template_type: str
    description: str = ""
    category: str = "other"
    tags: list[str] = field(default_factory=list)
    status: str = "active"  # active|archived|deleted
    featured: bool = False
    current_version: str = "1.0.0"
    asset_uri: str = ""
    library_id: str | None = None
    downloads: int = 0
    rating_total: int = 0
    rating_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    archived_at: datetime | None = None
    deleted_at: datetime | None = None
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    @property
    def avg_rating(self) -> float:
        return round(self.rating_total / self.rating_count, 2) if self.rating_count else 0.0

    def to_dict(self, *, include_asset_uri: bool = False) -> dict[str, Any]:
        data = {
            "id": self.id,
            "organizationId": self.organization_id,
            "ownerUserId": self.owner_user_id,
            "name": self.name,
            "slug": self.slug,
            "templateType": self.template_type,
            "description": self.description,
            "category": self.category,
            "tags": list(self.tags),
            "status": self.status,
            "featured": self.featured,
            "currentVersion": self.current_version,
            "libraryId": self.library_id,
            "downloads": self.downloads,
            "avgRating": self.avg_rating,
            "ratings": self.rating_count,
            "metadata": dict(self.metadata),
            "archivedAt": _iso(self.archived_at),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }
        if include_asset_uri:
            data["assetUri"] = self.asset_uri
        return data


@dataclass
class AssetLibrary:
    id: str
    organization_id: str
    owner_user_id: str
    name: str
    slug: str
    description: str = ""
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "ownerUserId": self.owner_user_id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class AssetCollectionRecord:
    id: str
    organization_id: str
    owner_user_id: str
    name: str
    slug: str
    description: str = ""
    template_ids: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "ownerUserId": self.owner_user_id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "templateIds": list(self.template_ids),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }
