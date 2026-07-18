"""Platform Administration & Operations APIs — Phase 7 Sprint 9.

Mounted under /api/admin alongside legacy fal guard routes in admin.py.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import platform_ops as po
from app.services.enterprise_auth.errors import AccessError
from app.services.multi_tenant.validation import ValidationError

router = APIRouter(prefix="/admin", tags=["platform-ops"])


def _auth(secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if expected and (secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _svc():
    return po.get_platform_ops_service()


def _map(exc: Exception) -> HTTPException:
    if isinstance(exc, AccessError):
        return HTTPException(
            status_code=exc.status_code,
            detail={"error": exc.code, "message": exc.message},
        )
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=500, detail="Platform ops failed")


def _user(user_id: str | None) -> str:
    if not user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    return user_id


class SettingsPatchRequest(BaseModel):
    settings: list[dict[str, Any]] | None = None
    updates: list[dict[str, Any]] | None = None
    key: str | None = None
    value: Any = None
    category: str | None = None
    is_secret: bool | None = Field(None, alias="isSecret")
    confirm: bool | None = None
    confirm_sensitive: bool | None = Field(None, alias="confirmSensitive")
    namespace: str | None = None
    config: dict[str, Any] | None = None
    model_config = {"populate_by_name": True}


class MaintenanceRequest(BaseModel):
    message: str | None = "Platform maintenance in progress"
    status: str = "active"
    disable: bool = False
    metadata: dict[str, Any] | None = None
    model_config = {"populate_by_name": True}


class RestartServicesRequest(BaseModel):
    services: list[str] | None = None
    model_config = {"populate_by_name": True}


@router.get("/ops/status")
async def platform_ops_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().status()


@router.get("/ops/observability")
async def platform_ops_observability(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().observability()


@router.get("/system")
async def admin_system(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().system.status(actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@router.get("/platform")
async def admin_platform(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().admin.platform(actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@router.get("/providers")
async def admin_providers(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().admin.providers(actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@router.get("/logs")
async def admin_logs(
    level: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().system.logs(actor_id=actor, level=level, limit=limit)
    except Exception as exc:
        raise _map(exc) from exc


@router.get("/settings")
async def admin_get_settings(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().config.get_settings(actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@router.patch("/settings")
async def admin_patch_settings(
    body: SettingsPatchRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().config.update_settings(
            body.model_dump(exclude_none=True, by_alias=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@router.post("/maintenance")
async def admin_maintenance(
    body: MaintenanceRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        if body.disable:
            return _svc().maintenance.disable(actor_id=actor)
        return _svc().maintenance.enable(body.model_dump(by_alias=True), actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@router.post("/cache/clear")
async def admin_cache_clear(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().system.clear_cache(actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@router.post("/system/restart-services")
async def admin_restart_services(
    body: RestartServicesRequest | None = None,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        services = body.services if body else None
        return _svc().system.restart_services(actor_id=actor, services=services)
    except Exception as exc:
        raise _map(exc) from exc
