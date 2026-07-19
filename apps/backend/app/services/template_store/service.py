"""Enterprise Template Store, Versioning & Asset Management Engine — Phase 9 Sprint 4.

Engines:
- TemplateStoreEngine (upload/update/delete/archive/duplicate/restore, ratings,
  downloads, featured)
- AssetVersioningEngine (version history, integrity checksums, rollback)
- AssetLibraryEngine (libraries and collections)
- CategoryManagementEngine (category taxonomy)
- TaggingEngine (tag registry with usage counts)
- SearchFilterEngine (full-text search + category/tag/creator/rating/
  popular/latest/featured filters)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.services.template_store import store
from app.services.template_store.catalog import (
    DEFAULT_CATEGORIES,
    MAX_SEARCH_RESULTS,
    MAX_TAGS_PER_TEMPLATE,
    RATING_MAX,
    RATING_MIN,
    SORT_MODES,
    TEMPLATE_STATUSES,
    TEMPLATE_TYPES,
    is_semver,
    slugify,
    tokenize,
    version_checksum,
)
from app.services.template_store.models import (
    AssetCollectionRecord,
    AssetLibrary,
    Template,
    TemplateVersion,
    new_id,
)
from app.services.template_store.version import (
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
        action, actor_id=actor_id, success=True, detail=detail or action, metadata=meta
    )


def _require_member(*, actor_id: str, organization_id: str) -> None:
    _require_access(
        user_id=actor_id, organization_id=organization_id, permission="org.read"
    )


def _require_manager(*, actor_id: str, organization_id: str) -> None:
    _require_access(
        user_id=actor_id, organization_id=organization_id, permission="org.update"
    )


def _seed_categories() -> None:
    if not store.list_categories():
        for slug, label in DEFAULT_CATEGORIES:
            store.upsert_category(slug, label)


def _index(template: Template) -> None:
    store.index_template(
        template.id,
        tokenize(
            template.name,
            template.description,
            template.category,
            template.template_type,
            " ".join(template.tags),
        ),
    )


def _clean_tags(raw: list[Any]) -> list[str]:
    ValidationError, _ = _validation()
    tags = sorted({str(t).strip().lower() for t in (raw or []) if str(t).strip()})
    if len(tags) > MAX_TAGS_PER_TEMPLATE:
        raise ValidationError(f"maximum {MAX_TAGS_PER_TEMPLATE} tags per template")
    return tags


class TemplateStoreEngine:
    """Template lifecycle: upload, update, archive, restore, duplicate, delete."""

    def _get_for_write(self, template_id: str, *, actor_id: str) -> Template:
        ForbiddenError, NotFoundError = _auth_errors()
        template = store.get_template(template_id)
        if template is None or template.status == "deleted":
            raise NotFoundError("template not found")
        if template.owner_user_id != actor_id:
            try:
                _require_manager(
                    actor_id=actor_id, organization_id=template.organization_id
                )
            except Exception:
                raise ForbiddenError("only the template owner can perform this action")
        return template

    def _get_for_read(self, template_id: str, *, actor_id: str) -> Template:
        _, NotFoundError = _auth_errors()
        template = store.get_template(template_id)
        if template is None or template.status == "deleted":
            raise NotFoundError("template not found")
        _require_member(
            actor_id=actor_id, organization_id=template.organization_id
        )
        return template

    def upload(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            _seed_categories()
            ValidationError, require_non_empty = _validation()
            org_id = str(
                require_non_empty(payload.get("organizationId"), "organizationId")
            )
            _require_member(actor_id=actor_id, organization_id=org_id)
            name = str(require_non_empty(payload.get("name"), "name"))
            template_type = str(payload.get("templateType") or "custom")
            if template_type not in TEMPLATE_TYPES:
                raise ValidationError(f"unknown template type: {template_type}")
            asset_uri = str(
                require_non_empty(payload.get("assetUri"), "assetUri")
            )
            category = str(payload.get("category") or "other")
            if not store.has_category(category):
                raise ValidationError(f"unknown category: {category}")
            tags = _clean_tags(payload.get("tags") or [])
            library_id = payload.get("libraryId")
            if library_id:
                library = store.get_library(str(library_id))
                if library is None or library.organization_id != org_id:
                    raise ValidationError(f"library not found: {library_id}")
            template = Template(
                id=new_id("tpl_"),
                organization_id=org_id,
                owner_user_id=actor_id,
                name=name,
                slug=slugify(name),
                template_type=template_type,
                description=str(payload.get("description") or ""),
                category=category,
                tags=tags,
                featured=bool(payload.get("featured") or False),
                asset_uri=asset_uri,
                library_id=str(library_id) if library_id else None,
                metadata=dict(payload.get("metadata") or {}),
            )
            store.save_template(template)
            version = TemplateVersion(
                id=new_id("tpv_"),
                template_id=template.id,
                version=template.current_version,
                changelog="Initial version",
                asset_uri=asset_uri,
                checksum=version_checksum(
                    template.id, template.current_version, asset_uri, name
                ),
                created_by=actor_id,
            )
            store.save_version(version)
            for tag in tags:
                store.bump_tag(tag)
            _index(template)
            _audit("template_store.uploaded", actor_id, name)
            return {"ok": True, "template": template.to_dict(include_asset_uri=True)}

    def get(self, template_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            template = self._get_for_read(template_id, actor_id=actor_id)
            return {
                "ok": True,
                "template": template.to_dict(include_asset_uri=True),
                "versions": [v.to_dict() for v in store.list_versions(template_id)],
            }

    def update(
        self, template_id: str, payload: dict[str, Any], *, actor_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            template = self._get_for_write(template_id, actor_id=actor_id)
            if "name" in payload and payload["name"] is not None:
                name = str(payload["name"]).strip()
                if not name:
                    raise ValidationError("name must not be empty")
                template.name = name
                template.slug = slugify(name)
            if "description" in payload and payload["description"] is not None:
                template.description = str(payload["description"])
            if "category" in payload and payload["category"] is not None:
                category = str(payload["category"])
                if not store.has_category(category):
                    raise ValidationError(f"unknown category: {category}")
                template.category = category
            if "tags" in payload and payload["tags"] is not None:
                new_tags = _clean_tags(payload["tags"])
                for tag in template.tags:
                    store.bump_tag(tag, -1)
                for tag in new_tags:
                    store.bump_tag(tag)
                template.tags = new_tags
            if "featured" in payload and payload["featured"] is not None:
                template.featured = bool(payload["featured"])
            if "metadata" in payload and payload["metadata"] is not None:
                template.metadata = dict(payload["metadata"])
            if "libraryId" in payload:
                library_id = payload["libraryId"]
                if library_id:
                    library = store.get_library(str(library_id))
                    if (
                        library is None
                        or library.organization_id != template.organization_id
                    ):
                        raise ValidationError(f"library not found: {library_id}")
                    template.library_id = str(library_id)
                else:
                    template.library_id = None
            template.updated_at = _now()
            store.save_template(template)
            _index(template)
            _audit("template_store.updated", actor_id, template.name)
            return {"ok": True, "template": template.to_dict(include_asset_uri=True)}

    def archive(self, template_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            template = self._get_for_write(template_id, actor_id=actor_id)
            if template.status == "archived":
                raise ValidationError("template is already archived")
            template.status = "archived"
            template.archived_at = _now()
            template.updated_at = _now()
            store.save_template(template)
            _audit("template_store.archived", actor_id, template.name)
            return {"ok": True, "template": template.to_dict()}

    def restore(self, template_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            template = self._get_for_write(template_id, actor_id=actor_id)
            if template.status != "archived":
                raise ValidationError("only archived templates can be restored")
            template.status = "active"
            template.archived_at = None
            template.updated_at = _now()
            store.save_template(template)
            _audit("template_store.restored", actor_id, template.name)
            return {"ok": True, "template": template.to_dict()}

    def delete(self, template_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            template = self._get_for_write(template_id, actor_id=actor_id)
            template.status = "deleted"
            template.deleted_at = _now()
            template.updated_at = _now()
            store.save_template(template)
            store.unindex_template(template_id)
            for tag in template.tags:
                store.bump_tag(tag, -1)
            _audit("template_store.deleted", actor_id, template.name)
            return {"ok": True, "templateId": template_id, "status": "deleted"}

    def duplicate(self, template_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            source = self._get_for_read(template_id, actor_id=actor_id)
            copy = Template(
                id=new_id("tpl_"),
                organization_id=source.organization_id,
                owner_user_id=actor_id,
                name=f"{source.name} (Copy)",
                slug=slugify(f"{source.name}-copy"),
                template_type=source.template_type,
                description=source.description,
                category=source.category,
                tags=list(source.tags),
                asset_uri=source.asset_uri,
                library_id=source.library_id,
                metadata=dict(source.metadata),
            )
            store.save_template(copy)
            store.save_version(
                TemplateVersion(
                    id=new_id("tpv_"),
                    template_id=copy.id,
                    version=copy.current_version,
                    changelog=f"Duplicated from {source.id}",
                    asset_uri=copy.asset_uri,
                    checksum=version_checksum(
                        copy.id, copy.current_version, copy.asset_uri, copy.name
                    ),
                    created_by=actor_id,
                )
            )
            for tag in copy.tags:
                store.bump_tag(tag)
            _index(copy)
            _audit("template_store.duplicated", actor_id, source.name)
            return {"ok": True, "template": copy.to_dict(include_asset_uri=True)}

    def rate(
        self, template_id: str, value: int, *, actor_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            template = self._get_for_read(template_id, actor_id=actor_id)
            if not (RATING_MIN <= value <= RATING_MAX):
                raise ValidationError(
                    f"rating must be between {RATING_MIN} and {RATING_MAX}"
                )
            if not store.save_rating(template_id, actor_id, value):
                raise ValidationError("template already rated by this user")
            template.rating_total += value
            template.rating_count += 1
            store.save_template(template)
            _audit("template_store.rated", actor_id, template.name, value=value)
            return {
                "ok": True,
                "templateId": template_id,
                "avgRating": template.avg_rating,
                "ratings": template.rating_count,
            }

    def record_download(self, template_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            template = self._get_for_read(template_id, actor_id=actor_id)
            template.downloads += 1
            store.save_template(template)
            return {
                "ok": True,
                "templateId": template_id,
                "downloads": template.downloads,
                "assetUri": template.asset_uri,
            }

    def list(
        self,
        *,
        actor_id: str,
        organization_id: str,
        status: str | None = None,
        owner: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            _require_member(actor_id=actor_id, organization_id=organization_id)
            if status is not None and status not in TEMPLATE_STATUSES:
                raise ValidationError(f"unknown status: {status}")
            items = store.list_templates(
                organization_id=organization_id, owner=owner, status=status
            )
            items.sort(key=lambda t: t.created_at, reverse=True)
            items = items[: max(1, min(limit, 500))]
            return {
                "ok": True,
                "count": len(items),
                "templates": [t.to_dict() for t in items],
            }


class AssetVersioningEngine:
    """Version history with integrity checksums and rollback."""

    def __init__(self, templates: TemplateStoreEngine) -> None:
        self._templates = templates

    def publish_version(
        self, template_id: str, payload: dict[str, Any], *, actor_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            template = self._templates._get_for_write(template_id, actor_id=actor_id)
            version = str(require_non_empty(payload.get("version"), "version"))
            if not is_semver(version):
                raise ValidationError("version must be semver (e.g. 1.2.0)")
            if store.get_version(template_id, version) is not None:
                raise ValidationError(f"version {version} already exists")
            asset_uri = str(payload.get("assetUri") or template.asset_uri)
            record = TemplateVersion(
                id=new_id("tpv_"),
                template_id=template_id,
                version=version,
                changelog=str(payload.get("changelog") or ""),
                asset_uri=asset_uri,
                checksum=version_checksum(
                    template_id, version, asset_uri, template.name
                ),
                created_by=actor_id,
            )
            store.save_version(record)
            template.current_version = version
            template.asset_uri = asset_uri
            template.updated_at = _now()
            store.save_template(template)
            _audit(
                "template_store.version_published", actor_id, template.name,
                version=version,
            )
            return {"ok": True, "version": record.to_dict()}

    def history(self, template_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            template = self._templates._get_for_read(template_id, actor_id=actor_id)
            versions = store.list_versions(template_id)
            return {
                "ok": True,
                "templateId": template_id,
                "currentVersion": template.current_version,
                "count": len(versions),
                "versions": [v.to_dict() for v in versions],
            }

    def verify_integrity(
        self, template_id: str, version: str, *, actor_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            _, NotFoundError = _auth_errors()
            template = self._templates._get_for_read(template_id, actor_id=actor_id)
            record = store.get_version(template_id, version)
            if record is None:
                raise NotFoundError(f"version not found: {version}")
            expected = version_checksum(
                template_id, version, record.asset_uri, template.name
            )
            valid = expected == record.checksum
            return {
                "ok": True,
                "templateId": template_id,
                "version": version,
                "valid": valid,
                "checksum": record.checksum,
            }

    def rollback(
        self, template_id: str, version: str, *, actor_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            _, NotFoundError = _auth_errors()
            template = self._templates._get_for_write(template_id, actor_id=actor_id)
            record = store.get_version(template_id, version)
            if record is None:
                raise NotFoundError(f"version not found: {version}")
            if template.current_version == version:
                raise ValidationError("template is already at this version")
            template.current_version = record.version
            template.asset_uri = record.asset_uri
            template.updated_at = _now()
            store.save_template(template)
            _audit(
                "template_store.rolled_back", actor_id, template.name,
                version=version,
            )
            return {
                "ok": True,
                "template": template.to_dict(include_asset_uri=True),
                "rolledBackTo": version,
            }


class AssetLibraryEngine:
    """Asset libraries and curated collections."""

    def create_library(
        self, payload: dict[str, Any], *, actor_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            _, require_non_empty = _validation()
            org_id = str(
                require_non_empty(payload.get("organizationId"), "organizationId")
            )
            _require_member(actor_id=actor_id, organization_id=org_id)
            name = str(require_non_empty(payload.get("name"), "name"))
            library = AssetLibrary(
                id=new_id("lib_"),
                organization_id=org_id,
                owner_user_id=actor_id,
                name=name,
                slug=slugify(name),
                description=str(payload.get("description") or ""),
            )
            store.save_library(library)
            _audit("template_store.library_created", actor_id, name)
            return {"ok": True, "library": library.to_dict()}

    def list_libraries(
        self, *, actor_id: str, organization_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            _require_member(actor_id=actor_id, organization_id=organization_id)
            libraries = store.list_libraries(organization_id)
            counts: dict[str, int] = {}
            for t in store.list_templates(organization_id=organization_id):
                if t.library_id:
                    counts[t.library_id] = counts.get(t.library_id, 0) + 1
            return {
                "ok": True,
                "count": len(libraries),
                "libraries": [
                    {**l.to_dict(), "templates": counts.get(l.id, 0)}
                    for l in libraries
                ],
            }

    def create_collection(
        self, payload: dict[str, Any], *, actor_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = str(
                require_non_empty(payload.get("organizationId"), "organizationId")
            )
            _require_member(actor_id=actor_id, organization_id=org_id)
            name = str(require_non_empty(payload.get("name"), "name"))
            template_ids: list[str] = []
            for tid in payload.get("templateIds") or []:
                template = store.get_template(str(tid))
                if (
                    template is None
                    or template.status == "deleted"
                    or template.organization_id != org_id
                ):
                    raise ValidationError(f"template not found: {tid}")
                template_ids.append(str(tid))
            collection = AssetCollectionRecord(
                id=new_id("col_"),
                organization_id=org_id,
                owner_user_id=actor_id,
                name=name,
                slug=slugify(name),
                description=str(payload.get("description") or ""),
                template_ids=template_ids,
            )
            store.save_collection(collection)
            _audit("template_store.collection_created", actor_id, name)
            return {"ok": True, "collection": collection.to_dict()}

    def list_collections(
        self, *, actor_id: str, organization_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            _require_member(actor_id=actor_id, organization_id=organization_id)
            collections = store.list_collections(organization_id)
            return {
                "ok": True,
                "count": len(collections),
                "collections": [c.to_dict() for c in collections],
            }


class CategoryManagementEngine:
    """Category taxonomy shared by all templates."""

    def list(self) -> dict[str, Any]:
        with store.timed_op():
            _seed_categories()
            categories = store.list_categories()
            usage: dict[str, int] = {}
            for t in store.list_templates():
                usage[t.category] = usage.get(t.category, 0) + 1
            return {
                "ok": True,
                "count": len(categories),
                "categories": [
                    {"slug": slug, "label": label, "templates": usage.get(slug, 0)}
                    for slug, label in sorted(categories.items())
                ],
            }

    def upsert(
        self, payload: dict[str, Any], *, actor_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            _seed_categories()
            _, require_non_empty = _validation()
            org_id = str(
                require_non_empty(payload.get("organizationId"), "organizationId")
            )
            _require_manager(actor_id=actor_id, organization_id=org_id)
            slug = slugify(str(require_non_empty(payload.get("slug"), "slug")))
            label = str(payload.get("label") or slug.title())
            store.upsert_category(slug, label)
            _audit("template_store.category_upserted", actor_id, slug)
            return {"ok": True, "category": {"slug": slug, "label": label}}


class TaggingEngine:
    """Tag registry with usage counts."""

    def list(self, *, limit: int = 100) -> dict[str, Any]:
        with store.timed_op():
            tags = sorted(
                store.list_tags().items(), key=lambda kv: kv[1], reverse=True
            )[: max(1, min(limit, 500))]
            return {
                "ok": True,
                "count": len(tags),
                "tags": [{"slug": slug, "usageCount": n} for slug, n in tags],
            }


class SearchFilterEngine:
    """Full-text search with category/tag/creator/rating/sort filters."""

    def search(
        self,
        *,
        actor_id: str,
        organization_id: str,
        query: str = "",
        category: str | None = None,
        tag: str | None = None,
        creator: str | None = None,
        template_type: str | None = None,
        min_rating: float = 0.0,
        featured_only: bool = False,
        sort: str = "latest",
        limit: int = 20,
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            _require_member(actor_id=actor_id, organization_id=organization_id)
            if sort not in SORT_MODES:
                raise ValidationError(f"unknown sort mode: {sort}")
            tokens = tokenize(query)
            results: list[tuple[float, Template]] = []
            for template in store.list_templates(
                organization_id=organization_id, status="active"
            ):
                if category and template.category != category:
                    continue
                if tag and tag.lower() not in template.tags:
                    continue
                if creator and template.owner_user_id != creator:
                    continue
                if template_type and template.template_type != template_type:
                    continue
                if template.avg_rating < min_rating:
                    continue
                if featured_only and not template.featured:
                    continue
                score = 1.0
                if tokens:
                    indexed = store.search_tokens(template.id)
                    matched = tokens & indexed
                    if not matched:
                        continue
                    score = len(matched) / len(tokens)
                results.append((score, template))

            if sort == "latest":
                results.sort(key=lambda st: st[1].created_at, reverse=True)
            elif sort == "popular":
                results.sort(key=lambda st: st[1].downloads, reverse=True)
            elif sort == "rating":
                results.sort(key=lambda st: st[1].avg_rating, reverse=True)
            elif sort == "featured":
                results.sort(
                    key=lambda st: (st[1].featured, st[1].downloads), reverse=True
                )
            if tokens:
                results.sort(key=lambda st: st[0], reverse=True)

            capped = results[: max(1, min(limit, MAX_SEARCH_RESULTS))]
            return {
                "ok": True,
                "count": len(capped),
                "query": query,
                "sort": sort,
                "results": [
                    {**t.to_dict(), "score": round(score, 3)} for score, t in capped
                ],
            }


class TemplateStoreFacade:
    """Facade combining all template store engines."""

    def __init__(self) -> None:
        self.templates = TemplateStoreEngine()
        self.versioning = AssetVersioningEngine(self.templates)
        self.libraries = AssetLibraryEngine()
        self.categories = CategoryManagementEngine()
        self.tags = TaggingEngine()
        self.search = SearchFilterEngine()

    def status(self) -> dict[str, Any]:
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "label": ENGINE_LABEL,
            "phase": PHASE,
            "sprint": SPRINT,
            "engines": {
                "templateStore": "ready",
                "assetVersioning": "ready",
                "assetLibrary": "ready",
                "categoryManagement": "ready",
                "tagging": "ready",
                "searchFilter": "ready",
            },
            "templateTypes": list(TEMPLATE_TYPES),
            "sortModes": list(SORT_MODES),
            "stats": store.metrics(),
        }


_service: TemplateStoreFacade | None = None


def get_template_store_service() -> TemplateStoreFacade:
    global _service
    if _service is None:
        _service = TemplateStoreFacade()
    return _service


def reset_engine() -> None:
    global _service
    store.reset_store()
    _service = None


get_engine = get_template_store_service
