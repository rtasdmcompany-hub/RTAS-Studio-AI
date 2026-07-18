"""Asset Management & Digital Library APIs — Phase 7 Sprint 5."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import asset_library as al
from app.services.enterprise_auth.errors import AccessError
from app.services.multi_tenant.validation import ValidationError

router = APIRouter(prefix="/assets", tags=["asset-library"])


def _auth(secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if expected and (secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _svc():
    return al.get_asset_library_service()


def _map(exc: Exception) -> HTTPException:
    if isinstance(exc, AccessError):
        return HTTPException(
            status_code=exc.status_code,
            detail={"error": exc.code, "message": exc.message},
        )
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=500, detail="Asset operation failed")


def _user(user_id: str | None) -> str:
    if not user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    return user_id


class UploadRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    name: str | None = None
    filename: str | None = None
    asset_type: str = Field("document", alias="assetType")
    mime_type: str | None = Field(None, alias="mimeType")
    category: str = "general"
    workspace_id: str | None = Field(None, alias="workspaceId")
    content: str | None = None
    url: str | None = None
    size_bytes: int | None = Field(None, alias="sizeBytes")
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None
    description: str | None = None
    title: str | None = None
    preview_url: str | None = Field(None, alias="previewUrl")
    model_config = {"populate_by_name": True}


class UpdateAssetRequest(BaseModel):
    name: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None
    model_config = {"populate_by_name": True}


class ShareRequest(BaseModel):
    asset_id: str = Field(..., alias="assetId")
    subject_type: str = Field("user", alias="subjectType")
    subject_id: str | None = Field(None, alias="subjectId")
    user_id: str | None = Field(None, alias="userId")
    role: str = "read"
    model_config = {"populate_by_name": True}


class TagRequest(BaseModel):
    tags: list[str]


class VersionRequest(BaseModel):
    content: str | None = None
    url: str | None = None
    size_bytes: int | None = Field(None, alias="sizeBytes")
    note: str | None = None
    model_config = {"populate_by_name": True}


@router.get("/status")
async def assets_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().status()


@router.get("/observability")
async def assets_observability(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().observability()


@router.post("/upload")
async def upload_asset(
    body: UploadRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().assets.upload(body.model_dump(by_alias=True), actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@router.get("")
async def list_assets(
    organization_id: str | None = Query(None, alias="organizationId"),
    workspace_id: str | None = Query(None, alias="workspaceId"),
    asset_type: str | None = Query(None, alias="assetType"),
    category: str | None = Query(None),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    try:
        return _svc().assets.list(
            {
                "organizationId": organization_id,
                "workspaceId": workspace_id,
                "assetType": asset_type,
                "category": category,
            },
            actor_id=x_rtas_user_id,
        )
    except Exception as exc:
        raise _map(exc) from exc


@router.get("/search")
async def search_assets(
    q: str | None = Query(None),
    organization_id: str | None = Query(None, alias="organizationId"),
    tag: str | None = Query(None),
    category: str | None = Query(None),
    asset_type: str | None = Query(None, alias="assetType"),
    semantic: bool = Query(False),
    metadata_key: str | None = Query(None, alias="metadataKey"),
    metadata_value: str | None = Query(None, alias="metadataValue"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    try:
        return _svc().search.search(
            {
                "q": q,
                "organizationId": organization_id,
                "tag": tag,
                "category": category,
                "assetType": asset_type,
                "semantic": semantic,
                "metadataKey": metadata_key,
                "metadataValue": metadata_value,
            },
            actor_id=x_rtas_user_id,
        )
    except Exception as exc:
        raise _map(exc) from exc


@router.get("/recent")
async def recent_assets(
    organization_id: str = Query(..., alias="organizationId"),
    limit: int = Query(20, ge=1, le=100),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().search.recent(
            organization_id=organization_id, actor_id=actor, limit=limit
        )
    except Exception as exc:
        raise _map(exc) from exc


@router.get("/favorites")
async def favorite_assets(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().search.favorites(organization_id=organization_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@router.post("/share")
async def share_asset(
    body: ShareRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().sharing.share(body.model_dump(by_alias=True), actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@router.get("/library")
async def digital_library(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().library.list_libraries(organization_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@router.get("/{asset_id}")
async def get_asset(
    asset_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().assets.get(asset_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@router.patch("/{asset_id}")
async def update_asset(
    asset_id: str,
    body: UpdateAssetRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().assets.update(
            asset_id, body.model_dump(exclude_none=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@router.delete("/{asset_id}")
async def delete_asset(
    asset_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().assets.delete(asset_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@router.post("/{asset_id}/download")
async def download_asset(
    asset_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().assets.download(asset_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@router.post("/{asset_id}/archive")
async def archive_asset(
    asset_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().assets.archive(asset_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@router.post("/{asset_id}/restore")
async def restore_asset(
    asset_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().assets.restore(asset_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@router.post("/{asset_id}/favorite")
async def favorite_asset(
    asset_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().assets.favorite(asset_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@router.post("/{asset_id}/duplicate")
async def duplicate_asset(
    asset_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().assets.duplicate(asset_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@router.post("/{asset_id}/tags")
async def tag_asset(
    asset_id: str,
    body: TagRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().tagging.tag(asset_id, body.tags, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@router.get("/{asset_id}/versions")
async def asset_versions(
    asset_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().versions.history(asset_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@router.post("/{asset_id}/versions")
async def add_version(
    asset_id: str,
    body: VersionRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().versions.add_version(
            asset_id, body.model_dump(by_alias=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@router.get("/{asset_id}/preview")
async def preview_asset(
    asset_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().metadata.preview(asset_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc
