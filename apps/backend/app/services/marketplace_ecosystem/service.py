"""Enterprise AI Marketplace Ecosystem Foundation — Phase 9 Sprint 1.

Engines:
- MarketplaceCoreEngine (facade)
- CreatorPlatformEngine (creator/publisher profiles)
- DigitalAssetRegistry (asset lifecycle: draft, publish, version, archive, delete)
- MarketplaceCatalogEngine (listing, categories, tags, collections)
- MarketplaceSearchFoundation (full-text + filtered search)
- MarketplaceSecurityEngine (ownership, isolation, secure publishing, audit)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.services.marketplace_ecosystem import store
from app.services.marketplace_ecosystem.catalog import (
    ASSET_STATUSES,
    ASSET_TYPES,
    CREATOR_TYPES,
    DEFAULT_CATEGORIES,
    MAX_ASSETS_PER_COLLECTION,
    MAX_TAGS_PER_ASSET,
    VISIBILITY_LEVELS,
    generate_creator_handle,
    is_semver,
    slugify,
)
from app.services.marketplace_ecosystem.models import (
    AssetCollection,
    AssetVersion,
    Creator,
    EcosystemAsset,
    new_id,
)
from app.services.marketplace_ecosystem.version import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    PHASE,
    SPRINT,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _validation():
    from app.services.multi_tenant.validation import ValidationError, require_non_empty

    return ValidationError, require_non_empty


def _auth_errors():
    from app.services.enterprise_auth.errors import ForbiddenError, NotFoundError

    return ForbiddenError, NotFoundError


def _require_access(**kwargs: Any) -> None:
    from app.services.enterprise_auth.middleware import require_access

    require_access(**kwargs)


def _audit(action: str, actor_id: str, detail: str | None = None, **meta: Any) -> None:
    from app.services.enterprise_auth.audit import log_auth_event

    log_auth_event(
        action,
        actor_id=actor_id,
        success=True,
        detail=detail or action,
        metadata=meta,
    )


def _require_member(*, actor_id: str, organization_id: str) -> None:
    _require_access(
        user_id=actor_id,
        organization_id=organization_id,
        permission="org.read",
    )


class MarketplaceSecurityEngine:
    """Ownership, isolation, and secure-publishing checks used by all engines."""

    def require_member(self, *, actor_id: str, organization_id: str) -> None:
        _require_member(actor_id=actor_id, organization_id=organization_id)

    def require_asset_owner(self, asset: EcosystemAsset, *, actor_id: str) -> None:
        ForbiddenError, _ = _auth_errors()
        if asset.owner_user_id == actor_id:
            return
        # Org managers may also manage assets in their organization
        try:
            _require_access(
                user_id=actor_id,
                organization_id=asset.organization_id,
                permission="org.update",
            )
        except Exception:
            raise ForbiddenError("only the asset owner can perform this action")

    def get_asset_checked(
        self, asset_id: str, *, actor_id: str, for_write: bool = False
    ) -> EcosystemAsset:
        _, NotFoundError = _auth_errors()
        asset = store.get_asset(asset_id)
        if asset is None or asset.status == "deleted":
            raise NotFoundError("asset not found")
        if for_write:
            self.require_asset_owner(asset, actor_id=actor_id)
        elif asset.visibility != "public" or asset.status != "published":
            # Non-public or unpublished assets require org membership
            _require_member(actor_id=actor_id, organization_id=asset.organization_id)
        return asset

    def validate_publish(self, asset: EcosystemAsset) -> None:
        ValidationError, _ = _validation()
        if not asset.asset_uri:
            raise ValidationError("assets require an assetUri before publishing")
        if asset.status == "deleted":
            raise ValidationError("deleted assets cannot be published")

    def audit(self, action: str, actor_id: str, detail: str | None = None, **meta: Any) -> None:
        _audit(action, actor_id, detail, **meta)

    def status(self) -> dict[str, Any]:
        return {
            "assetOwnership": "enforced",
            "organizationIsolation": "enforced",
            "securePublishing": "enforced",
            "auditLogging": "enabled",
        }


class CreatorPlatformEngine:
    """Creator and publisher profile management."""

    def __init__(self, security: MarketplaceSecurityEngine) -> None:
        self._security = security

    def register(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = str(
                require_non_empty(
                    payload.get("organizationId") or payload.get("organization_id"),
                    "organizationId",
                )
            )
            self._security.require_member(actor_id=actor_id, organization_id=org_id)
            existing = store.get_creator_by_user(org_id, actor_id)
            if existing is not None:
                raise ValidationError("creator profile already exists for this user")
            display_name = str(
                require_non_empty(payload.get("displayName"), "displayName")
            )
            creator_type = str(payload.get("creatorType") or "creator")
            if creator_type not in CREATOR_TYPES:
                raise ValidationError(f"unknown creator type: {creator_type}")
            creator = Creator(
                id=new_id("mcr_"),
                user_id=actor_id,
                organization_id=org_id,
                display_name=display_name,
                handle=generate_creator_handle(display_name),
                creator_type=creator_type,
                bio=str(payload.get("bio") or ""),
                website=str(payload.get("website") or ""),
                metadata=dict(payload.get("metadata") or {}),
            )
            store.save_creator(creator)
            self._security.audit(
                "marketplace_ecosystem.creator_registered", actor_id, display_name
            )
            return {"ok": True, "creator": creator.to_dict()}

    def profile(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        with store.timed_op():
            _, NotFoundError = _auth_errors()
            self._security.require_member(
                actor_id=actor_id, organization_id=organization_id
            )
            creator = store.get_creator_by_user(organization_id, actor_id)
            if creator is None:
                raise NotFoundError("creator profile not found")
            assets = store.list_assets(creator_id=creator.id)
            return {
                "ok": True,
                "creator": creator.to_dict(),
                "assets": {
                    "total": len(assets),
                    "draft": sum(1 for a in assets if a.status == "draft"),
                    "published": sum(1 for a in assets if a.status == "published"),
                    "archived": sum(1 for a in assets if a.status == "archived"),
                },
            }

    def update_profile(
        self, payload: dict[str, Any], *, actor_id: str, organization_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            _, NotFoundError = _auth_errors()
            self._security.require_member(
                actor_id=actor_id, organization_id=organization_id
            )
            creator = store.get_creator_by_user(organization_id, actor_id)
            if creator is None:
                raise NotFoundError("creator profile not found")
            if "displayName" in payload:
                name = str(payload["displayName"] or "").strip()
                if not name:
                    raise ValidationError("displayName must not be empty")
                creator.display_name = name
            if "bio" in payload:
                creator.bio = str(payload["bio"] or "")
            if "website" in payload:
                creator.website = str(payload["website"] or "")
            if "creatorType" in payload:
                ctype = str(payload["creatorType"] or "")
                if ctype not in CREATOR_TYPES:
                    raise ValidationError(f"unknown creator type: {ctype}")
                creator.creator_type = ctype
            creator.updated_at = _now()
            store.save_creator(creator)
            self._security.audit(
                "marketplace_ecosystem.creator_updated", actor_id, creator.display_name
            )
            return {"ok": True, "creator": creator.to_dict()}

    def _ensure_creator(self, organization_id: str, actor_id: str) -> Creator:
        """Auto-provision a creator profile on first publish."""
        creator = store.get_creator_by_user(organization_id, actor_id)
        if creator is None:
            creator = Creator(
                id=new_id("mcr_"),
                user_id=actor_id,
                organization_id=organization_id,
                display_name=actor_id,
                handle=generate_creator_handle(actor_id),
            )
            store.save_creator(creator)
        return creator


class DigitalAssetRegistry:
    """Asset lifecycle: create draft, update, publish, version, archive, delete."""

    def __init__(
        self, security: MarketplaceSecurityEngine, creators: CreatorPlatformEngine
    ) -> None:
        self._security = security
        self._creators = creators

    def create(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = str(
                require_non_empty(
                    payload.get("organizationId") or payload.get("organization_id"),
                    "organizationId",
                )
            )
            self._security.require_member(actor_id=actor_id, organization_id=org_id)
            name = str(require_non_empty(payload.get("name"), "name"))
            asset_type = str(payload.get("assetType") or "custom")
            if asset_type not in ASSET_TYPES:
                raise ValidationError(f"unknown asset type: {asset_type}")
            category = str(payload.get("category") or "other")
            if category not in DEFAULT_CATEGORIES:
                raise ValidationError(f"unknown category: {category}")
            visibility = str(payload.get("visibility") or "public")
            if visibility not in VISIBILITY_LEVELS:
                raise ValidationError(f"unknown visibility: {visibility}")
            tags = [
                str(t).strip().lower()
                for t in (payload.get("tags") or [])
                if str(t).strip()
            ]
            if len(tags) > MAX_TAGS_PER_ASSET:
                raise ValidationError(f"maximum {MAX_TAGS_PER_ASSET} tags per asset")
            creator = self._creators._ensure_creator(org_id, actor_id)
            asset = EcosystemAsset(
                id=new_id("mka_"),
                organization_id=org_id,
                creator_id=creator.id,
                owner_user_id=actor_id,
                name=name,
                slug=slugify(name),
                asset_type=asset_type,
                description=str(payload.get("description") or ""),
                category=category,
                tags=sorted(set(tags)),
                visibility=visibility,
                asset_uri=str(payload.get("assetUri") or ""),
                workspace_id=payload.get("workspaceId"),
                metadata=dict(payload.get("metadata") or {}),
            )
            store.save_asset(asset)
            store.save_version(
                AssetVersion(
                    id=new_id("mkv_"),
                    asset_id=asset.id,
                    version=asset.current_version,
                    changelog="Initial version",
                    asset_uri=asset.asset_uri,
                    created_by=actor_id,
                )
            )
            creator.total_versions += 1
            store.save_creator(creator)
            if bool(payload.get("publish")):
                self._publish(asset, actor_id=actor_id)
            self._security.audit(
                "marketplace_ecosystem.asset_created", actor_id, name,
                assetType=asset_type,
            )
            return {"ok": True, "asset": asset.to_dict(include_asset_uri=True)}

    def _publish(self, asset: EcosystemAsset, *, actor_id: str) -> None:
        self._security.validate_publish(asset)
        asset.status = "published"
        asset.published_at = _now()
        asset.archived_at = None
        asset.updated_at = _now()
        store.save_asset(asset)
        creator = store.get_creator(asset.creator_id)
        if creator is not None:
            creator.published_assets = len(
                store.list_assets(creator_id=creator.id, status="published")
            )
            store.save_creator(creator)
        self._security.audit(
            "marketplace_ecosystem.asset_published", actor_id, asset.name
        )

    def update(
        self, asset_id: str, payload: dict[str, Any], *, actor_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            asset = self._security.get_asset_checked(
                asset_id, actor_id=actor_id, for_write=True
            )
            if "name" in payload and payload["name"] is not None:
                name = str(payload["name"]).strip()
                if not name:
                    raise ValidationError("name must not be empty")
                asset.name = name
                asset.slug = slugify(name)
            if "description" in payload and payload["description"] is not None:
                asset.description = str(payload["description"])
            if "category" in payload and payload["category"] is not None:
                category = str(payload["category"])
                if category not in DEFAULT_CATEGORIES:
                    raise ValidationError(f"unknown category: {category}")
                asset.category = category
            if "tags" in payload and payload["tags"] is not None:
                tags = [
                    str(t).strip().lower()
                    for t in payload["tags"]
                    if str(t).strip()
                ]
                if len(tags) > MAX_TAGS_PER_ASSET:
                    raise ValidationError(
                        f"maximum {MAX_TAGS_PER_ASSET} tags per asset"
                    )
                asset.tags = sorted(set(tags))
            if "visibility" in payload and payload["visibility"] is not None:
                visibility = str(payload["visibility"])
                if visibility not in VISIBILITY_LEVELS:
                    raise ValidationError(f"unknown visibility: {visibility}")
                asset.visibility = visibility
            if "assetUri" in payload and payload["assetUri"] is not None:
                asset.asset_uri = str(payload["assetUri"])

            # New version release
            if payload.get("version"):
                version = str(payload["version"])
                if not is_semver(version):
                    raise ValidationError("version must be semver (e.g. 1.2.0)")
                if any(
                    v.version == version for v in store.list_versions(asset.id)
                ):
                    raise ValidationError(f"version {version} already exists")
                store.save_version(
                    AssetVersion(
                        id=new_id("mkv_"),
                        asset_id=asset.id,
                        version=version,
                        changelog=str(payload.get("changelog") or ""),
                        asset_uri=asset.asset_uri,
                        created_by=actor_id,
                    )
                )
                asset.current_version = version
                creator = store.get_creator(asset.creator_id)
                if creator is not None:
                    creator.total_versions += 1
                    store.save_creator(creator)

            # Status transitions
            if payload.get("status"):
                target = str(payload["status"])
                if target not in ASSET_STATUSES or target == "deleted":
                    raise ValidationError(f"invalid status transition: {target}")
                if target == "published":
                    self._publish(asset, actor_id=actor_id)
                elif target == "archived":
                    asset.status = "archived"
                    asset.archived_at = _now()
                    self._security.audit(
                        "marketplace_ecosystem.asset_archived", actor_id, asset.name
                    )
                elif target == "draft":
                    asset.status = "draft"
                    asset.published_at = None
                    asset.archived_at = None

            asset.updated_at = _now()
            store.save_asset(asset)
            self._security.audit(
                "marketplace_ecosystem.asset_updated", actor_id, asset.name
            )
            return {"ok": True, "asset": asset.to_dict(include_asset_uri=True)}

    def delete(self, asset_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            asset = self._security.get_asset_checked(
                asset_id, actor_id=actor_id, for_write=True
            )
            asset.status = "deleted"
            asset.deleted_at = _now()
            asset.updated_at = _now()
            store.save_asset(asset)
            creator = store.get_creator(asset.creator_id)
            if creator is not None:
                creator.published_assets = len(
                    store.list_assets(creator_id=creator.id, status="published")
                )
                store.save_creator(creator)
            self._security.audit(
                "marketplace_ecosystem.asset_deleted", actor_id, asset.name
            )
            return {"ok": True, "assetId": asset_id, "status": "deleted"}

    def get(self, asset_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            asset = self._security.get_asset_checked(asset_id, actor_id=actor_id)
            include_uri = asset.owner_user_id == actor_id
            return {"ok": True, "asset": asset.to_dict(include_asset_uri=include_uri)}

    def versions(self, asset_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            asset = self._security.get_asset_checked(asset_id, actor_id=actor_id)
            items = store.list_versions(asset.id)
            return {
                "ok": True,
                "assetId": asset.id,
                "count": len(items),
                "versions": [v.to_dict() for v in items],
            }


class MarketplaceCatalogEngine:
    """Asset listing, categories, tags, and collections."""

    def __init__(self, security: MarketplaceSecurityEngine) -> None:
        self._security = security

    def list(
        self,
        *,
        actor_id: str | None = None,
        organization_id: str | None = None,
        status: str | None = None,
        asset_type: str | None = None,
        category: str | None = None,
        tag: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        with store.timed_op():
            if organization_id and actor_id:
                # Org-scoped listings expose drafts/archived — require membership
                self._security.require_member(
                    actor_id=actor_id, organization_id=organization_id
                )
                items = store.list_assets(
                    organization_id=organization_id,
                    status=status,
                    asset_type=asset_type,
                    category=category,
                )
            else:
                # Public catalog: only published + public assets
                items = [
                    a
                    for a in store.list_assets(
                        status="published", asset_type=asset_type, category=category
                    )
                    if a.visibility == "public"
                ]
            if tag:
                needle = tag.strip().lower()
                items = [a for a in items if needle in a.tags]
            items = items[: max(1, min(limit, 200))]
            return {
                "ok": True,
                "count": len(items),
                "assets": [a.to_dict() for a in items],
            }

    def categories(self) -> dict[str, Any]:
        with store.timed_op():
            published = [
                a
                for a in store.list_assets(status="published")
                if a.visibility == "public"
            ]
            counts = {c: 0 for c in DEFAULT_CATEGORIES}
            for a in published:
                counts[a.category] = counts.get(a.category, 0) + 1
            return {
                "ok": True,
                "count": len(DEFAULT_CATEGORIES),
                "categories": [
                    {"key": c, "assetCount": counts.get(c, 0)}
                    for c in DEFAULT_CATEGORIES
                ],
            }

    def tags(self) -> dict[str, Any]:
        with store.timed_op():
            counts: dict[str, int] = {}
            for a in store.list_assets(status="published"):
                if a.visibility != "public":
                    continue
                for t in a.tags:
                    counts[t] = counts.get(t, 0) + 1
            top = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:100]
            return {
                "ok": True,
                "count": len(top),
                "tags": [{"tag": t, "assetCount": n} for t, n in top],
            }

    def create_collection(
        self, payload: dict[str, Any], *, actor_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            _, NotFoundError = _auth_errors()
            org_id = str(
                require_non_empty(
                    payload.get("organizationId") or payload.get("organization_id"),
                    "organizationId",
                )
            )
            self._security.require_member(actor_id=actor_id, organization_id=org_id)
            creator = store.get_creator_by_user(org_id, actor_id)
            if creator is None:
                raise NotFoundError("creator profile required to create collections")
            name = str(require_non_empty(payload.get("name"), "name"))
            asset_ids = [str(a) for a in (payload.get("assetIds") or [])]
            if len(asset_ids) > MAX_ASSETS_PER_COLLECTION:
                raise ValidationError(
                    f"maximum {MAX_ASSETS_PER_COLLECTION} assets per collection"
                )
            for aid in asset_ids:
                asset = store.get_asset(aid)
                if asset is None or asset.status == "deleted":
                    raise ValidationError(f"asset not found: {aid}")
                if asset.organization_id != org_id:
                    raise ValidationError(
                        "collections may only contain assets from the same organization"
                    )
            collection = AssetCollection(
                id=new_id("mkc_"),
                organization_id=org_id,
                creator_id=creator.id,
                name=name,
                slug=slugify(name),
                description=str(payload.get("description") or ""),
                asset_ids=asset_ids,
            )
            store.save_collection(collection)
            self._security.audit(
                "marketplace_ecosystem.collection_created", actor_id, name
            )
            return {"ok": True, "collection": collection.to_dict()}

    def list_collections(
        self, *, actor_id: str, organization_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            self._security.require_member(
                actor_id=actor_id, organization_id=organization_id
            )
            items = store.list_collections(organization_id=organization_id)
            return {
                "ok": True,
                "count": len(items),
                "collections": [c.to_dict() for c in items],
            }


class MarketplaceSearchFoundation:
    """Full-text search with type/category/tag filters over the public catalog."""

    def search(
        self,
        query: str = "",
        *,
        asset_type: str | None = None,
        category: str | None = None,
        tag: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        with store.timed_op():
            items = [
                a
                for a in store.list_assets(
                    status="published", asset_type=asset_type, category=category
                )
                if a.visibility == "public"
            ]
            if tag:
                needle_tag = tag.strip().lower()
                items = [a for a in items if needle_tag in a.tags]
            needle = (query or "").strip().lower()
            if needle:
                scored: list[tuple[int, EcosystemAsset]] = []
                for a in items:
                    score = 0
                    name = a.name.lower()
                    if needle in name:
                        score += 10
                        if name.startswith(needle):
                            score += 5
                    if needle in a.description.lower():
                        score += 3
                    if any(needle in t for t in a.tags):
                        score += 4
                    if needle in a.slug:
                        score += 2
                    if score > 0:
                        scored.append((score, a))
                scored.sort(key=lambda x: (-x[0], x[1].created_at))
                items = [a for _, a in scored]
            items = items[: max(1, min(limit, 200))]
            return {
                "ok": True,
                "query": query,
                "count": len(items),
                "results": [a.to_dict() for a in items],
            }


class MarketplaceCoreEngine:
    """Facade combining creators, registry, catalog, search, and security."""

    def __init__(self) -> None:
        self.security = MarketplaceSecurityEngine()
        self.creators = CreatorPlatformEngine(self.security)
        self.registry = DigitalAssetRegistry(self.security, self.creators)
        self.catalog = MarketplaceCatalogEngine(self.security)
        self.search = MarketplaceSearchFoundation()

    def status(self) -> dict[str, Any]:
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "label": ENGINE_LABEL,
            "phase": PHASE,
            "sprint": SPRINT,
            "engines": {
                "marketplaceCore": "ready",
                "creatorPlatform": "ready",
                "digitalAssetRegistry": "ready",
                "marketplaceCatalog": "ready",
                "marketplaceSearch": "ready",
                "marketplaceSecurity": "ready",
            },
            "assetTypes": list(ASSET_TYPES),
            "categories": list(DEFAULT_CATEGORIES),
            "security": self.security.status(),
            "stats": store.metrics(),
        }


_service: MarketplaceCoreEngine | None = None


def get_marketplace_ecosystem_service() -> MarketplaceCoreEngine:
    global _service
    if _service is None:
        _service = MarketplaceCoreEngine()
    return _service


def reset_engine() -> None:
    global _service
    store.reset_store()
    _service = None


get_engine = get_marketplace_ecosystem_service
