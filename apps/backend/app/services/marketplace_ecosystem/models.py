"""Domain models for creators, ecosystem assets, versions, and collections."""

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
class Creator:
    id: str
    user_id: str
    organization_id: str
    display_name: str
    handle: str
    creator_type: str = "creator"  # creator|publisher
    bio: str = ""
    website: str = ""
    status: str = "active"  # active|suspended
    published_assets: int = 0
    total_versions: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "userId": self.user_id,
            "organizationId": self.organization_id,
            "displayName": self.display_name,
            "handle": self.handle,
            "creatorType": self.creator_type,
            "bio": self.bio,
            "website": self.website,
            "status": self.status,
            "stats": {
                "publishedAssets": self.published_assets,
                "totalVersions": self.total_versions,
            },
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class AssetVersion:
    id: str
    asset_id: str
    version: str
    changelog: str = ""
    asset_uri: str = ""
    created_by: str = ""
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "assetId": self.asset_id,
            "version": self.version,
            "changelog": self.changelog,
            "assetUri": self.asset_uri,
            "createdBy": self.created_by,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class EcosystemAsset:
    id: str
    organization_id: str
    creator_id: str
    owner_user_id: str
    name: str
    slug: str
    asset_type: str
    description: str = ""
    category: str = "other"
    tags: list[str] = field(default_factory=list)
    status: str = "draft"  # draft|published|archived|deleted
    visibility: str = "public"  # public|organization|private
    current_version: str = "1.0.0"
    asset_uri: str = ""
    workspace_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    published_at: datetime | None = None
    archived_at: datetime | None = None
    deleted_at: datetime | None = None
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self, *, include_asset_uri: bool = False) -> dict[str, Any]:
        data = {
            "id": self.id,
            "organizationId": self.organization_id,
            "creatorId": self.creator_id,
            "ownerUserId": self.owner_user_id,
            "name": self.name,
            "slug": self.slug,
            "assetType": self.asset_type,
            "description": self.description,
            "category": self.category,
            "tags": list(self.tags),
            "status": self.status,
            "visibility": self.visibility,
            "currentVersion": self.current_version,
            "workspaceId": self.workspace_id,
            "metadata": dict(self.metadata),
            "publishedAt": _iso(self.published_at),
            "archivedAt": _iso(self.archived_at),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }
        if include_asset_uri:
            data["assetUri"] = self.asset_uri
        return data


@dataclass
class AssetCollection:
    id: str
    organization_id: str
    creator_id: str
    name: str
    slug: str
    description: str = ""
    asset_ids: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "creatorId": self.creator_id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "assetIds": list(self.asset_ids),
            "assetCount": len(self.asset_ids),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }
