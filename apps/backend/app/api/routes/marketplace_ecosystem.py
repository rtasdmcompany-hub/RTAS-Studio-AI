"""AI Marketplace Ecosystem Foundation APIs — Phase 9 Sprint 1."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.backend_auth import require_backend_secret
from app.core.config import settings
from app.services import marketplace_ecosystem as eco_svc
from app.services.enterprise_auth.errors import AccessError
from app.services.multi_tenant.validation import ValidationError

ecosystem_router = APIRouter(prefix="/marketplace", tags=["marketplace-ecosystem"])


def _auth(secret: str | None) -> None:
    require_backend_secret(x_rtas_backend_secret=secret)


def _svc():
    return eco_svc.get_marketplace_ecosystem_service()


def _map(exc: Exception) -> HTTPException:
    if isinstance(exc, AccessError):
        return HTTPException(
            status_code=exc.status_code,
            detail={"error": exc.code, "message": exc.message},
        )
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=500, detail="Marketplace ecosystem operation failed")


def _user(user_id: str | None) -> str:
    if not user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    return user_id


class AssetCreateRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    name: str
    asset_type: str = Field("custom", alias="assetType")
    description: str = ""
    category: str = "other"
    tags: list[str] = Field(default_factory=list)
    visibility: str = "public"
    asset_uri: str | None = Field(None, alias="assetUri")
    workspace_id: str | None = Field(None, alias="workspaceId")
    publish: bool = False
    model_config = {"populate_by_name": True}


class AssetUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    visibility: str | None = None
    asset_uri: str | None = Field(None, alias="assetUri")
    version: str | None = None
    changelog: str | None = None
    status: str | None = None
    model_config = {"populate_by_name": True}


class CreatorRegisterRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    display_name: str = Field(..., alias="displayName")
    creator_type: str = Field("creator", alias="creatorType")
    bio: str = ""
    website: str = ""
    model_config = {"populate_by_name": True}


class CreatorUpdateRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    display_name: str | None = Field(None, alias="displayName")
    creator_type: str | None = Field(None, alias="creatorType")
    bio: str | None = None
    website: str | None = None
    model_config = {"populate_by_name": True}


class CollectionCreateRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    name: str
    description: str = ""
    asset_ids: list[str] = Field(default_factory=list, alias="assetIds")
    model_config = {"populate_by_name": True}


# --- Assets (static paths first, then dynamic) ---


@ecosystem_router.get("/assets/search")
async def search_assets(
    q: str = Query(""),
    asset_type: str | None = Query(None, alias="assetType"),
    category: str | None = Query(None),
    tag: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    try:
        return _svc().search.search(
            q, asset_type=asset_type, category=category, tag=tag, limit=limit
        )
    except Exception as exc:
        raise _map(exc) from exc


@ecosystem_router.get("/assets/categories")
async def list_asset_categories():
    try:
        return _svc().catalog.categories()
    except Exception as exc:
        raise _map(exc) from exc


@ecosystem_router.get("/assets/tags")
async def list_asset_tags():
    try:
        return _svc().catalog.tags()
    except Exception as exc:
        raise _map(exc) from exc


@ecosystem_router.get("/assets")
async def list_assets(
    organization_id: str | None = Query(None, alias="organizationId"),
    status: str | None = Query(None),
    asset_type: str | None = Query(None, alias="assetType"),
    category: str | None = Query(None),
    tag: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    try:
        return _svc().catalog.list(
            actor_id=x_rtas_user_id,
            organization_id=organization_id,
            status=status,
            asset_type=asset_type,
            category=category,
            tag=tag,
            limit=limit,
        )
    except Exception as exc:
        raise _map(exc) from exc


@ecosystem_router.post("/assets")
async def create_asset(
    body: AssetCreateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().registry.create(
            body.model_dump(by_alias=True, exclude_none=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@ecosystem_router.get("/assets/{asset_id}")
async def get_asset(
    asset_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().registry.get(asset_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@ecosystem_router.patch("/assets/{asset_id}")
async def update_asset(
    asset_id: str,
    body: AssetUpdateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().registry.update(
            asset_id,
            body.model_dump(by_alias=True, exclude_unset=True),
            actor_id=actor,
        )
    except Exception as exc:
        raise _map(exc) from exc


@ecosystem_router.delete("/assets/{asset_id}")
async def delete_asset(
    asset_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().registry.delete(asset_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@ecosystem_router.get("/assets/{asset_id}/versions")
async def list_asset_versions(
    asset_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().registry.versions(asset_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


# --- Creators ---


@ecosystem_router.post("/creators/register")
async def register_creator(
    body: CreatorRegisterRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().creators.register(
            body.model_dump(by_alias=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@ecosystem_router.get("/creators/profile")
async def creator_profile(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().creators.profile(actor_id=actor, organization_id=organization_id)
    except Exception as exc:
        raise _map(exc) from exc


@ecosystem_router.patch("/creators/profile")
async def update_creator_profile(
    body: CreatorUpdateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        payload = body.model_dump(by_alias=True, exclude_unset=True)
        organization_id = payload.pop("organizationId")
        return _svc().creators.update_profile(
            payload, actor_id=actor, organization_id=organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


# --- Collections ---


@ecosystem_router.post("/collections")
async def create_collection(
    body: CollectionCreateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().catalog.create_collection(
            body.model_dump(by_alias=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@ecosystem_router.get("/collections")
async def list_collections(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().catalog.list_collections(
            actor_id=actor, organization_id=organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


# --- Status ---


@ecosystem_router.get("/ecosystem/status")
async def ecosystem_status():
    return _svc().status()
