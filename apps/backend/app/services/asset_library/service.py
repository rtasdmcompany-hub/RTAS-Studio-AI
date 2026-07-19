"""Enterprise Asset Management & Digital Library Engine — Phase 7 Sprint 5."""

from __future__ import annotations

import hashlib
import hmac
import re
import time
from base64 import urlsafe_b64encode
from datetime import datetime, timedelta, timezone
from typing import Any

from app.services.asset_library import store
from app.services.asset_library.catalog import (
    ASSET_TYPES,
    PERMISSION_ROLES,
    SYSTEM_CATEGORIES,
    normalize_asset_type,
    role_at_least,
)
from app.services.asset_library.models import (
    AssetActivity,
    AssetCollection,
    AssetPermission,
    AssetVersion,
    LibraryAsset,
    new_id,
)
from app.services.asset_library.version import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    MAX_ASSETS_PER_ORG,
    MAX_VERSIONS_PER_ASSET,
    PHASE,
    SIGNED_URL_TTL_SEC,
    SPRINT,
)
from app.services.enterprise_auth.audit import log_auth_event
from app.services.enterprise_auth.errors import ForbiddenError, NotFoundError, UnauthorizedError
from app.services.enterprise_auth.middleware import require_access
from app.services.multi_tenant.repository import get_repository
from app.services.multi_tenant.validation import ValidationError, normalize_slug, require_non_empty


def _signing_secret() -> bytes:
    from app.core.signing_secrets import asset_library_signing_secret

    return asset_library_signing_secret()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _slug_from_name(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "asset"
    return base[:64]


def _checksum(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()[:32]


def _tokens(text: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9_]+", text.lower()) if t}


def _log(asset_id: str, actor_id: str, action: str, detail: str | None = None, **meta: Any) -> None:
    store.add_activity(
        AssetActivity(
            id=new_id("aact_"),
            asset_id=asset_id,
            actor_id=actor_id,
            action=action,
            detail=detail,
            metadata=dict(meta),
        )
    )
    log_auth_event(
        action,
        actor_id=actor_id,
        success=True,
        detail=detail or action,
        metadata={"assetId": asset_id, **meta},
    )


class AssetPermissionsEngine:
    def resolve_role(self, asset: LibraryAsset, user_id: str) -> str | None:
        if asset.owner_id == user_id:
            return "owner"
        perm = store.get_permission(asset.id, "user", user_id)
        if perm:
            return perm.role
        # org-level share
        org_perm = store.get_permission(asset.id, "organization", asset.organization_id)
        if org_perm and asset.is_shared:
            return org_perm.role
        if asset.workspace_id:
            ws_perm = store.get_permission(asset.id, "workspace", asset.workspace_id)
            if ws_perm:
                return ws_perm.role
        # org members get read on shared assets
        member = get_repository().get_member_by_org_user(asset.organization_id, user_id)
        if member and asset.is_shared and member.status == "active":
            return "read"
        return None

    def require(
        self, asset_id: str, user_id: str, required: str = "read"
    ) -> tuple[LibraryAsset, str]:
        asset = store.get_asset(asset_id)
        if asset is None or (asset.status == "deleted" and required != "owner"):
            raise NotFoundError("asset not found")
        role = self.resolve_role(asset, user_id)
        if role is None or not role_at_least(role, required):
            raise ForbiddenError(f"missing asset permission: {required}")
        return asset, role


class AssetManagementEngine:
    def __init__(self) -> None:
        self.perms = AssetPermissionsEngine()

    def upload(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            org_id = require_non_empty(
                payload.get("organizationId") or payload.get("organization_id"),
                "organizationId",
            )
            require_access(
                user_id=actor_id,
                organization_id=org_id,
                workspace_id=payload.get("workspaceId") or payload.get("workspace_id"),
                permission="content.write",
            )
            workspace_id = payload.get("workspaceId") or payload.get("workspace_id")
            if workspace_id:
                ws = get_repository().get_workspace(str(workspace_id))
                if ws is None or ws.organization_id != org_id:
                    raise ForbiddenError("workspace isolation violation")
            name = require_non_empty(payload.get("name") or payload.get("filename"), "name", max_len=200)
            try:
                asset_type = normalize_asset_type(str(payload.get("assetType") or payload.get("type") or "document"))
            except ValueError as exc:
                raise ValidationError(str(exc)) from exc
            slug = normalize_slug(payload.get("slug") or _slug_from_name(name))
            if store.get_by_slug(org_id, slug):
                slug = f"{slug}-{new_id('')[:8]}"
            if len(store.list_assets(organization_id=org_id, include_deleted=True)) >= MAX_ASSETS_PER_ORG:
                raise ValidationError("asset limit reached")
            content = str(payload.get("content") or payload.get("url") or payload.get("data") or "")
            size = int(payload.get("sizeBytes") or payload.get("size") or len(content.encode("utf-8")))
            storage_key = f"org/{org_id}/{slug}/v1"
            asset = LibraryAsset(
                id=new_id("asset_"),
                organization_id=org_id,
                workspace_id=str(workspace_id) if workspace_id else None,
                owner_id=str(payload.get("ownerId") or actor_id),
                name=name,
                slug=slug,
                asset_type=asset_type,
                mime_type=payload.get("mimeType") or payload.get("mime_type"),
                category=str(payload.get("category") or "general").lower(),
                storage_key=storage_key,
                storage_url=payload.get("url") or payload.get("storageUrl"),
                size_bytes=size,
                checksum=_checksum(content or storage_key),
                tags=[str(t).lower() for t in (payload.get("tags") or [])],
                metadata=dict(payload.get("metadata") or {}),
                preview_url=payload.get("previewUrl") or payload.get("preview_url"),
                content_ref=content or None,
            )
            if payload.get("description"):
                asset.metadata["description"] = str(payload["description"])
            if payload.get("title"):
                asset.metadata["title"] = str(payload["title"])
            # semantic hint for AI search
            asset.metadata["embeddingHint"] = " ".join(
                [
                    asset.name,
                    asset.asset_type,
                    asset.category,
                    " ".join(asset.tags),
                    str(asset.metadata.get("description") or ""),
                ]
            ).lower()
            store.save_asset(asset)
            store.save_version(
                AssetVersion(
                    id=new_id("aver_"),
                    asset_id=asset.id,
                    version=1,
                    storage_key=storage_key,
                    storage_url=asset.storage_url,
                    size_bytes=size,
                    checksum=asset.checksum,
                    created_by_id=actor_id,
                    note="initial upload",
                    content_ref=asset.content_ref,
                )
            )
            store.save_permission(
                AssetPermission(
                    id=new_id("aperm_"),
                    asset_id=asset.id,
                    subject_type="user",
                    subject_id=asset.owner_id,
                    role="owner",
                )
            )
            store.record_upload()
            _log(asset.id, actor_id, "asset.uploaded", asset.name, assetType=asset_type)
            return {"ok": True, "asset": asset.to_dict()}

    def list(self, filters: dict[str, Any] | None = None, *, actor_id: str | None = None) -> dict[str, Any]:
        filters = filters or {}
        org_id = filters.get("organizationId") or filters.get("organization_id")
        if actor_id and org_id:
            require_access(user_id=actor_id, organization_id=str(org_id), permission="content.read")
        items = store.list_assets(
            organization_id=str(org_id) if org_id else None,
            workspace_id=filters.get("workspaceId") or filters.get("workspace_id"),
            owner_id=filters.get("ownerId") or filters.get("owner_id"),
            asset_type=filters.get("assetType") or filters.get("type"),
            category=filters.get("category"),
            status=filters.get("status"),
            favorite_only=bool(filters.get("favorites")),
        )
        return {"ok": True, "count": len(items), "assets": [a.to_dict() for a in items]}

    def get(self, asset_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            asset, role = self.perms.require(asset_id, actor_id, "read")
            require_access(
                user_id=actor_id,
                organization_id=asset.organization_id,
                workspace_id=asset.workspace_id,
                permission="content.read",
            )
            return {
                "ok": True,
                "asset": asset.to_dict(),
                "role": role,
                "versions": [v.to_dict() for v in store.list_versions(asset_id)],
                "permissions": [p.to_dict() for p in store.list_permissions(asset_id)],
            }

    def update(self, asset_id: str, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            asset, _ = self.perms.require(asset_id, actor_id, "edit")
            if payload.get("name"):
                asset.name = require_non_empty(payload["name"], "name", max_len=200)
            if payload.get("category"):
                asset.category = str(payload["category"]).lower()
            if payload.get("metadata") is not None:
                if not isinstance(payload["metadata"], dict):
                    raise ValidationError("metadata must be an object")
                asset.metadata.update(dict(payload["metadata"]))
            if "tags" in payload and isinstance(payload["tags"], list):
                asset.tags = [str(t).lower() for t in payload["tags"]]
            asset.updated_at = _now()
            store.save_asset(asset)
            _log(asset_id, actor_id, "asset.updated", asset.name)
            return {"ok": True, "asset": asset.to_dict()}

    def rename(self, asset_id: str, name: str, *, actor_id: str) -> dict[str, Any]:
        return self.update(asset_id, {"name": name}, actor_id=actor_id)

    def move(
        self,
        asset_id: str,
        *,
        actor_id: str,
        workspace_id: str | None = None,
        category: str | None = None,
    ) -> dict[str, Any]:
        asset, _ = self.perms.require(asset_id, actor_id, "edit")
        if workspace_id:
            ws = get_repository().get_workspace(workspace_id)
            if ws is None or ws.organization_id != asset.organization_id:
                raise ForbiddenError("workspace isolation violation")
            asset.workspace_id = workspace_id
        if category:
            asset.category = category.lower()
        asset.updated_at = _now()
        store.save_asset(asset)
        _log(asset_id, actor_id, "asset.moved", detail=workspace_id or category)
        return {"ok": True, "asset": asset.to_dict()}

    def copy(self, asset_id: str, *, actor_id: str) -> dict[str, Any]:
        asset, _ = self.perms.require(asset_id, actor_id, "read")
        return self.upload(
            {
                "organizationId": asset.organization_id,
                "workspaceId": asset.workspace_id,
                "name": f"{asset.name} (Copy)",
                "assetType": asset.asset_type,
                "mimeType": asset.mime_type,
                "category": asset.category,
                "tags": list(asset.tags),
                "metadata": dict(asset.metadata),
                "content": asset.content_ref or asset.storage_key,
                "sizeBytes": asset.size_bytes,
                "url": asset.storage_url,
            },
            actor_id=actor_id,
        )

    def duplicate(self, asset_id: str, *, actor_id: str) -> dict[str, Any]:
        return self.copy(asset_id, actor_id=actor_id)

    def archive(self, asset_id: str, *, actor_id: str) -> dict[str, Any]:
        asset, _ = self.perms.require(asset_id, actor_id, "edit")
        asset.status = "archived"
        asset.archived_at = _now()
        asset.updated_at = _now()
        store.save_asset(asset)
        _log(asset_id, actor_id, "asset.archived")
        return {"ok": True, "asset": asset.to_dict()}

    def restore(self, asset_id: str, *, actor_id: str) -> dict[str, Any]:
        asset = store.get_asset(asset_id)
        if asset is None:
            raise NotFoundError("asset not found")
        role = self.perms.resolve_role(asset, actor_id)
        if role is None or not role_at_least(role, "edit"):
            raise ForbiddenError("missing asset permission: edit")
        asset.status = "active"
        asset.archived_at = None
        asset.deleted_at = None
        asset.updated_at = _now()
        store.save_asset(asset)
        _log(asset_id, actor_id, "asset.restored")
        return {"ok": True, "asset": asset.to_dict()}

    def delete(self, asset_id: str, *, actor_id: str) -> dict[str, Any]:
        asset, role = self.perms.require(asset_id, actor_id, "owner")
        if role != "owner" and asset.owner_id != actor_id:
            raise ForbiddenError("asset ownership required")
        asset.status = "deleted"
        asset.deleted_at = _now()
        asset.updated_at = _now()
        store.save_asset(asset)
        _log(asset_id, actor_id, "asset.deleted")
        return {"ok": True, "deleted": True, "asset": asset.to_dict()}

    def favorite(self, asset_id: str, *, actor_id: str, favorite: bool = True) -> dict[str, Any]:
        asset, _ = self.perms.require(asset_id, actor_id, "read")
        asset.is_favorite = bool(favorite)
        asset.updated_at = _now()
        store.save_asset(asset)
        return {"ok": True, "asset": asset.to_dict()}

    def download(self, asset_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            asset, _ = self.perms.require(asset_id, actor_id, "read")
            signed = SignedUrlEngine().sign(asset_id, actor_id=actor_id)
            asset.download_count += 1
            asset.use_count += 1
            asset.updated_at = _now()
            store.save_asset(asset)
            store.record_download()
            _log(asset_id, actor_id, "asset.downloaded")
            return {
                "ok": True,
                "assetId": asset_id,
                "downloadUrl": signed["url"],
                "expiresAt": signed["expiresAt"],
                "storageUrl": asset.storage_url,
                "contentRef": asset.content_ref,
            }


class AssetVersionManager:
    def __init__(self) -> None:
        self.perms = AssetPermissionsEngine()

    def add_version(
        self, asset_id: str, payload: dict[str, Any], *, actor_id: str
    ) -> dict[str, Any]:
        asset, _ = self.perms.require(asset_id, actor_id, "edit")
        versions = store.list_versions(asset_id)
        if len(versions) >= MAX_VERSIONS_PER_ASSET:
            raise ValidationError("version limit reached")
        next_ver = (versions[0].version if versions else asset.current_version) + 1
        content = str(payload.get("content") or payload.get("url") or "")
        storage_key = f"org/{asset.organization_id}/{asset.slug}/v{next_ver}"
        ver = AssetVersion(
            id=new_id("aver_"),
            asset_id=asset_id,
            version=next_ver,
            storage_key=storage_key,
            storage_url=payload.get("url") or payload.get("storageUrl"),
            size_bytes=int(payload.get("sizeBytes") or len(content.encode("utf-8"))),
            checksum=_checksum(content or storage_key),
            note=payload.get("note"),
            created_by_id=actor_id,
            content_ref=content or None,
        )
        store.save_version(ver)
        asset.current_version = next_ver
        asset.storage_key = storage_key
        asset.storage_url = ver.storage_url
        asset.size_bytes = ver.size_bytes
        asset.checksum = ver.checksum
        asset.content_ref = ver.content_ref
        asset.updated_at = _now()
        store.save_asset(asset)
        _log(asset_id, actor_id, "asset.version_added", detail=str(next_ver))
        return {"ok": True, "version": ver.to_dict(), "asset": asset.to_dict()}

    def history(self, asset_id: str, *, actor_id: str) -> dict[str, Any]:
        self.perms.require(asset_id, actor_id, "read")
        items = store.list_versions(asset_id)
        return {"ok": True, "count": len(items), "versions": [v.to_dict() for v in items]}


class AssetTaggingEngine:
    def __init__(self) -> None:
        self.perms = AssetPermissionsEngine()

    def tag(self, asset_id: str, tags: list[str], *, actor_id: str) -> dict[str, Any]:
        asset, _ = self.perms.require(asset_id, actor_id, "edit")
        merged = sorted(set(asset.tags) | {str(t).lower().strip() for t in tags if str(t).strip()})
        asset.tags = merged
        asset.updated_at = _now()
        store.save_asset(asset)
        _log(asset_id, actor_id, "asset.tagged", detail=",".join(tags))
        return {"ok": True, "asset": asset.to_dict()}

    def categorize(self, asset_id: str, category: str, *, actor_id: str) -> dict[str, Any]:
        asset, _ = self.perms.require(asset_id, actor_id, "edit")
        asset.category = require_non_empty(category, "category", max_len=64).lower()
        asset.updated_at = _now()
        store.save_asset(asset)
        return {"ok": True, "asset": asset.to_dict()}


class AssetSearchEngine:
    def search(self, payload: dict[str, Any], *, actor_id: str | None = None) -> dict[str, Any]:
        start = time.perf_counter()
        org_id = payload.get("organizationId") or payload.get("organization_id")
        if actor_id and org_id:
            require_access(user_id=actor_id, organization_id=str(org_id), permission="content.read")
        query = str(payload.get("q") or payload.get("query") or "").strip().lower()
        tag = payload.get("tag")
        category = payload.get("category")
        asset_type = payload.get("assetType") or payload.get("type")
        semantic = bool(payload.get("semantic"))
        items = store.list_assets(
            organization_id=str(org_id) if org_id else None,
            workspace_id=payload.get("workspaceId") or payload.get("workspace_id"),
            asset_type=str(asset_type).lower() if asset_type else None,
            category=str(category).lower() if category else None,
        )
        if tag:
            t = str(tag).lower()
            items = [a for a in items if t in a.tags]
        if query:
            q_tokens = _tokens(query)
            scored: list[tuple[float, LibraryAsset]] = []
            for a in items:
                hay = " ".join(
                    [
                        a.name,
                        a.slug,
                        a.asset_type,
                        a.category,
                        " ".join(a.tags),
                        str(a.metadata.get("title") or ""),
                        str(a.metadata.get("description") or ""),
                        str(a.metadata.get("embeddingHint") or ""),
                    ]
                ).lower()
                if semantic:
                    a_tokens = _tokens(hay)
                    overlap = len(q_tokens & a_tokens)
                    score = overlap / max(len(q_tokens), 1)
                    if query in hay:
                        score += 0.5
                    if score > 0:
                        scored.append((score, a))
                elif query in hay or any(tok in hay for tok in q_tokens):
                    scored.append((1.0, a))
            scored.sort(key=lambda x: x[0], reverse=True)
            items = [a for _, a in scored]
        # metadata field search
        meta_key = payload.get("metadataKey")
        meta_value = payload.get("metadataValue")
        if meta_key and meta_value:
            items = [
                a
                for a in items
                if str(a.metadata.get(str(meta_key), "")).lower()
                == str(meta_value).lower()
            ]
        ms = (time.perf_counter() - start) * 1000
        store.record_search(ms)
        return {
            "ok": True,
            "count": len(items),
            "query": query or None,
            "semantic": semantic,
            "latencyMs": round(ms, 2),
            "assets": [a.to_dict() for a in items[:100]],
        }

    def recent(self, *, organization_id: str, actor_id: str, limit: int = 20) -> dict[str, Any]:
        require_access(user_id=actor_id, organization_id=organization_id, permission="content.read")
        items = store.list_assets(organization_id=organization_id)
        items.sort(key=lambda a: a.updated_at, reverse=True)
        return {
            "ok": True,
            "count": min(len(items), limit),
            "assets": [a.to_dict() for a in items[:limit]],
        }

    def most_used(self, *, organization_id: str, actor_id: str, limit: int = 20) -> dict[str, Any]:
        require_access(user_id=actor_id, organization_id=organization_id, permission="content.read")
        items = store.list_assets(organization_id=organization_id)
        items.sort(key=lambda a: (a.use_count, a.download_count), reverse=True)
        return {
            "ok": True,
            "count": min(len(items), limit),
            "assets": [a.to_dict() for a in items[:limit]],
        }

    def favorites(self, *, organization_id: str, actor_id: str) -> dict[str, Any]:
        require_access(user_id=actor_id, organization_id=organization_id, permission="content.read")
        items = store.list_assets(organization_id=organization_id, favorite_only=True)
        return {"ok": True, "count": len(items), "assets": [a.to_dict() for a in items]}


class AssetSharingEngine:
    def __init__(self) -> None:
        self.perms = AssetPermissionsEngine()

    def share(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            asset_id = require_non_empty(
                payload.get("assetId") or payload.get("asset_id"), "assetId"
            )
            asset, _ = self.perms.require(asset_id, actor_id, "edit")
            subject_type = str(payload.get("subjectType") or payload.get("subject_type") or "user").lower()
            role = str(payload.get("role") or "read").lower()
            if role not in PERMISSION_ROLES or role == "owner":
                raise ValidationError("role must be read or edit")
            raw_subject = (
                payload.get("subjectId")
                or payload.get("subject_id")
                or payload.get("userId")
            )
            if subject_type == "organization":
                subject_id = asset.organization_id
                asset.is_shared = True
            elif subject_type == "workspace":
                if not asset.workspace_id:
                    raise ValidationError("asset has no workspace")
                subject_id = str(raw_subject or asset.workspace_id)
                asset.is_shared = True
            elif subject_type == "team":
                subject_id = require_non_empty(raw_subject, "subjectId")
                asset.is_shared = True
            elif subject_type == "user":
                subject_id = require_non_empty(raw_subject, "subjectId")
                member = get_repository().get_member_by_org_user(
                    asset.organization_id, subject_id
                )
                if member is None:
                    raise ForbiddenError("user is not in organization")
                asset.is_shared = True
            else:
                raise ValidationError("subjectType must be user|team|workspace|organization")
            existing = store.get_permission(asset_id, subject_type, subject_id)
            if existing:
                existing.role = role
                store.save_permission(existing)
                perm = existing
            else:
                perm = AssetPermission(
                    id=new_id("aperm_"),
                    asset_id=asset_id,
                    subject_type=subject_type,
                    subject_id=subject_id,
                    role=role,
                )
                store.save_permission(perm)
            asset.updated_at = _now()
            store.save_asset(asset)
            _log(asset_id, actor_id, "asset.shared", detail=f"{subject_type}:{subject_id}:{role}")
            return {"ok": True, "permission": perm.to_dict(), "asset": asset.to_dict()}


class AssetMetadataEngine:
    def __init__(self) -> None:
        self.perms = AssetPermissionsEngine()

    def update(self, asset_id: str, metadata: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        asset, _ = self.perms.require(asset_id, actor_id, "edit")
        if not isinstance(metadata, dict):
            raise ValidationError("metadata must be an object")
        asset.metadata.update(metadata)
        asset.metadata["embeddingHint"] = " ".join(
            [
                asset.name,
                asset.asset_type,
                asset.category,
                " ".join(asset.tags),
                str(asset.metadata.get("description") or ""),
                str(asset.metadata.get("title") or ""),
            ]
        ).lower()
        asset.updated_at = _now()
        store.save_asset(asset)
        return {"ok": True, "asset": asset.to_dict()}

    def preview(self, asset_id: str, *, actor_id: str) -> dict[str, Any]:
        asset, _ = self.perms.require(asset_id, actor_id, "read")
        return {
            "ok": True,
            "assetId": asset_id,
            "previewUrl": asset.preview_url or asset.storage_url,
            "mimeType": asset.mime_type,
            "assetType": asset.asset_type,
            "name": asset.name,
            "metadata": dict(asset.metadata),
        }


class SignedUrlEngine:
    def sign(self, asset_id: str, *, actor_id: str, ttl_sec: int = SIGNED_URL_TTL_SEC) -> dict[str, Any]:
        expires = int(time.time()) + max(60, ttl_sec)
        payload = f"{asset_id}:{actor_id}:{expires}"
        sig = hmac.new(_signing_secret(), payload.encode(), hashlib.sha256).hexdigest()[:32]
        token = urlsafe_b64encode(f"{payload}:{sig}".encode()).decode().rstrip("=")
        return {
            "url": f"/api/assets/{asset_id}/download?token={token}",
            "token": token,
            "expiresAt": datetime.fromtimestamp(expires, tz=timezone.utc).isoformat().replace("+00:00", "Z"),
        }

    def verify(self, asset_id: str, token: str, *, actor_id: str | None = None) -> bool:
        try:
            padded = token + "=" * (-len(token) % 4)
            from base64 import urlsafe_b64decode

            raw = urlsafe_b64decode(padded.encode()).decode()
            aid, uid, expires_s, sig = raw.rsplit(":", 3)
            if aid != asset_id:
                return False
            if actor_id and uid != actor_id:
                return False
            if int(expires_s) < int(time.time()):
                return False
            payload = f"{aid}:{uid}:{expires_s}"
            expected = hmac.new(_signing_secret(), payload.encode(), hashlib.sha256).hexdigest()[:32]
            return hmac.compare_digest(expected, sig)
        except Exception:
            return False


class DigitalLibraryEngine:
    def create_collection(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        org_id = require_non_empty(
            payload.get("organizationId") or payload.get("organization_id"),
            "organizationId",
        )
        require_access(user_id=actor_id, organization_id=org_id, permission="content.write")
        name = require_non_empty(payload.get("name"), "name", max_len=120)
        scope = str(payload.get("libraryScope") or payload.get("scope") or "organization").lower()
        if scope not in {"organization", "workspace", "team"}:
            raise ValidationError("libraryScope must be organization|workspace|team")
        col = AssetCollection(
            id=new_id("acol_"),
            organization_id=org_id,
            workspace_id=payload.get("workspaceId") or payload.get("workspace_id"),
            name=name,
            slug=normalize_slug(payload.get("slug") or _slug_from_name(name)),
            library_scope=scope,
            description=payload.get("description"),
        )
        store.save_collection(col)
        return {"ok": True, "collection": col.to_dict()}

    def add_to_collection(
        self, collection_id: str, asset_id: str, *, actor_id: str
    ) -> dict[str, Any]:
        col = store.get_collection(collection_id)
        if col is None:
            raise NotFoundError("collection not found")
        require_access(
            user_id=actor_id, organization_id=col.organization_id, permission="content.write"
        )
        AssetPermissionsEngine().require(asset_id, actor_id, "read")
        if asset_id not in col.asset_ids:
            col.asset_ids.append(asset_id)
            store.save_collection(col)
        return {"ok": True, "collection": col.to_dict()}

    def list_libraries(self, organization_id: str, *, actor_id: str) -> dict[str, Any]:
        require_access(user_id=actor_id, organization_id=organization_id, permission="content.read")
        cols = store.list_collections(organization_id)
        return {
            "ok": True,
            "organizationLibrary": True,
            "workspaceLibrary": True,
            "teamLibrary": True,
            "collections": [c.to_dict() for c in cols],
            "categories": SYSTEM_CATEGORIES,
            "assetTypes": list(ASSET_TYPES),
        }


class AssetLibraryService:
    def __init__(self) -> None:
        self.assets = AssetManagementEngine()
        self.library = DigitalLibraryEngine()
        self.versions = AssetVersionManager()
        self.tagging = AssetTaggingEngine()
        self.search = AssetSearchEngine()
        self.sharing = AssetSharingEngine()
        self.metadata = AssetMetadataEngine()
        self.signed_urls = SignedUrlEngine()

    def status(self) -> dict[str, Any]:
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "label": ENGINE_LABEL,
            "phase": PHASE,
            "sprint": SPRINT,
            "modules": [
                "asset_management_engine",
                "digital_library_engine",
                "asset_version_manager",
                "asset_tagging_engine",
                "asset_search_engine",
                "asset_sharing_engine",
                "asset_metadata_engine",
            ],
            "assetTypes": list(ASSET_TYPES),
            "permissionRoles": list(PERMISSION_ROLES),
            "categories": SYSTEM_CATEGORIES,
            "stats": store.metrics(),
            "engines": {
                "asset": "ready",
                "library": "ready",
                "versions": "ready",
                "tagging": "ready",
                "search": "ready",
                "sharing": "ready",
                "metadata": "ready",
            },
        }

    def observability(self) -> dict[str, Any]:
        m = store.metrics()
        return {
            "ok": True,
            "totalAssets": m["totalAssets"],
            "storageUsage": m["storageUsageBytes"],
            "uploadSuccess": m["uploadSuccess"],
            "downloadSuccess": m["downloadSuccess"],
            "searchPerformanceMs": m["searchAvgMs"],
            "assetActivity": m["activityEvents"],
            "versionCount": m["versionCount"],
            "errors": m["errors"],
            "apiPerformance": {
                "calls": m["apiCalls"],
                "avgLatencyMs": m["avgLatencyMs"],
            },
        }


_service: AssetLibraryService | None = None


def get_asset_library_service() -> AssetLibraryService:
    global _service
    if _service is None:
        _service = AssetLibraryService()
    return _service


def reset_engine() -> None:
    global _service
    store.reset_store()
    from app.services.multi_tenant.engine import reset_engine as reset_mt
    from app.services.enterprise_auth.engine import reset_engine as reset_ea

    reset_mt()
    reset_ea()
    _service = None


get_engine = get_asset_library_service
