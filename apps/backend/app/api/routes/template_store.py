"""Template Store, Versioning & Asset Management APIs — Phase 9 Sprint 4."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import template_store as ts_svc
from app.services.enterprise_auth.errors import AccessError
from app.services.multi_tenant.validation import ValidationError

templates_router = APIRouter(prefix="/templates", tags=["template-store"])


def _auth(secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if expected and (secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _svc():
    return ts_svc.get_template_store_service()


def _map(exc: Exception) -> HTTPException:
    if isinstance(exc, AccessError):
        return HTTPException(
            status_code=exc.status_code,
            detail={"error": exc.code, "message": exc.message},
        )
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=500, detail="Template store operation failed")


def _user(user_id: str | None) -> str:
    if not user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    return user_id


class TemplateCreateRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    name: str
    template_type: str = Field("custom", alias="templateType")
    description: str = ""
    category: str = "other"
    tags: list[str] = Field(default_factory=list)
    asset_uri: str = Field(..., alias="assetUri")
    featured: bool = False
    library_id: str | None = Field(None, alias="libraryId")
    metadata: dict[str, Any] = Field(default_factory=dict)
    model_config = {"populate_by_name": True}


class TemplateUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    featured: bool | None = None
    library_id: str | None = Field(None, alias="libraryId")
    metadata: dict[str, Any] | None = None
    model_config = {"populate_by_name": True}


class VersionPublishRequest(BaseModel):
    version: str
    changelog: str = ""
    asset_uri: str | None = Field(None, alias="assetUri")
    model_config = {"populate_by_name": True}


class RollbackRequest(BaseModel):
    version: str


class RatingRequest(BaseModel):
    value: int


class LibraryCreateRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    name: str
    description: str = ""
    model_config = {"populate_by_name": True}


class CollectionCreateRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    name: str
    description: str = ""
    template_ids: list[str] = Field(default_factory=list, alias="templateIds")
    model_config = {"populate_by_name": True}


class CategoryUpsertRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    slug: str
    label: str = ""
    model_config = {"populate_by_name": True}


# --- Static routes (declared before /{template_id}) ---


@templates_router.get("/search")
async def search_templates(
    organization_id: str = Query(..., alias="organizationId"),
    q: str = Query(""),
    category: str | None = Query(None),
    tag: str | None = Query(None),
    creator: str | None = Query(None),
    template_type: str | None = Query(None, alias="templateType"),
    min_rating: float = Query(0.0, alias="minRating", ge=0, le=5),
    featured_only: bool = Query(False, alias="featuredOnly"),
    sort: str = Query("latest"),
    limit: int = Query(20, ge=1, le=100),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().search.search(
            actor_id=actor,
            organization_id=organization_id,
            query=q,
            category=category,
            tag=tag,
            creator=creator,
            template_type=template_type,
            min_rating=min_rating,
            featured_only=featured_only,
            sort=sort,
            limit=limit,
        )
    except Exception as exc:
        raise _map(exc) from exc


@templates_router.get("/categories")
async def list_categories():
    try:
        return _svc().categories.list()
    except Exception as exc:
        raise _map(exc) from exc


@templates_router.post("/categories")
async def upsert_category(
    body: CategoryUpsertRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().categories.upsert(
            body.model_dump(by_alias=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@templates_router.get("/tags")
async def list_tags(limit: int = Query(100, ge=1, le=500)):
    try:
        return _svc().tags.list(limit=limit)
    except Exception as exc:
        raise _map(exc) from exc


@templates_router.post("/libraries")
async def create_library(
    body: LibraryCreateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().libraries.create_library(
            body.model_dump(by_alias=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@templates_router.get("/libraries")
async def list_libraries(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().libraries.list_libraries(
            actor_id=actor, organization_id=organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@templates_router.post("/collections")
async def create_collection(
    body: CollectionCreateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().libraries.create_collection(
            body.model_dump(by_alias=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@templates_router.get("/collections")
async def list_collections(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().libraries.list_collections(
            actor_id=actor, organization_id=organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@templates_router.get("/status")
async def template_store_status():
    return _svc().status()


# --- Template CRUD ---


@templates_router.post("")
async def create_template(
    body: TemplateCreateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().templates.upload(
            body.model_dump(by_alias=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@templates_router.get("")
async def list_templates(
    organization_id: str = Query(..., alias="organizationId"),
    status: str | None = Query(None),
    owner: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().templates.list(
            actor_id=actor,
            organization_id=organization_id,
            status=status,
            owner=owner,
            limit=limit,
        )
    except Exception as exc:
        raise _map(exc) from exc


@templates_router.get("/{template_id}")
async def get_template(
    template_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().templates.get(template_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@templates_router.patch("/{template_id}")
async def update_template(
    template_id: str,
    body: TemplateUpdateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().templates.update(
            template_id,
            body.model_dump(by_alias=True, exclude_unset=True),
            actor_id=actor,
        )
    except Exception as exc:
        raise _map(exc) from exc


@templates_router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().templates.delete(template_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


# --- Lifecycle actions ---


@templates_router.post("/{template_id}/archive")
async def archive_template(
    template_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().templates.archive(template_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@templates_router.post("/{template_id}/restore")
async def restore_template(
    template_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().templates.restore(template_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@templates_router.post("/{template_id}/duplicate")
async def duplicate_template(
    template_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().templates.duplicate(template_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@templates_router.post("/{template_id}/rate")
async def rate_template(
    template_id: str,
    body: RatingRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().templates.rate(template_id, body.value, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@templates_router.post("/{template_id}/download")
async def download_template(
    template_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().templates.record_download(template_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


# --- Versioning ---


@templates_router.post("/{template_id}/versions")
async def publish_version(
    template_id: str,
    body: VersionPublishRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().versioning.publish_version(
            template_id, body.model_dump(by_alias=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@templates_router.get("/{template_id}/versions")
async def version_history(
    template_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().versioning.history(template_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@templates_router.get("/{template_id}/versions/{version}/verify")
async def verify_version_integrity(
    template_id: str,
    version: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().versioning.verify_integrity(
            template_id, version, actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@templates_router.post("/{template_id}/rollback")
async def rollback_template(
    template_id: str,
    body: RollbackRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().versioning.rollback(template_id, body.version, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc
