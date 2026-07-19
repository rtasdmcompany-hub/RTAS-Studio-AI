"""License & developer platform APIs — Phase 8 Sprint 7."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.backend_auth import require_backend_secret
from app.core.config import settings
from app.services import license_platform as lp_svc
from app.services.enterprise_auth.errors import AccessError
from app.services.multi_tenant.validation import ValidationError

licenses_router = APIRouter(prefix="/licenses", tags=["licenses"])
developer_router = APIRouter(prefix="/developer", tags=["developer"])


def _auth(secret: str | None) -> None:
    require_backend_secret(x_rtas_backend_secret=secret)


def _svc():
    return lp_svc.get_license_platform_service()


def _map(exc: Exception) -> HTTPException:
    if isinstance(exc, AccessError):
        return HTTPException(
            status_code=exc.status_code,
            detail={"error": exc.code, "message": exc.message},
        )
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=500, detail="License/developer operation failed")


def _user(user_id: str | None) -> str:
    if not user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    return user_id


class LicenseActivateRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    tier: str = "free"
    seats: int = 1
    model_config = {"populate_by_name": True}


class LicenseRenewRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    tier: str | None = None
    model_config = {"populate_by_name": True}


class LicenseRevokeRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    reason: str | None = None
    model_config = {"populate_by_name": True}


class LicenseValidateRequest(BaseModel):
    license_key: str = Field(..., alias="licenseKey")
    model_config = {"populate_by_name": True}


class ApiKeyCreateRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    key_type: str = Field("personal", alias="keyType")
    access: str = "full_access"
    name: str | None = None
    scopes: list[str] | None = None
    workspace_id: str | None = Field(None, alias="workspaceId")
    model_config = {"populate_by_name": True}


class TokenCreateRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    name: str | None = None
    scopes: list[str] | None = None
    expires_in_days: int | None = Field(None, alias="expiresInDays")
    model_config = {"populate_by_name": True}


class WebhookCreateRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    url: str
    events: list[str]
    model_config = {"populate_by_name": True}


# --- Licenses ---


@licenses_router.post("/activate")
async def activate_license(
    body: LicenseActivateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().licenses.activate(body.model_dump(by_alias=True), actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@licenses_router.get("/status")
async def license_status(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().licenses.status(actor_id=actor, organization_id=organization_id)
    except Exception as exc:
        raise _map(exc) from exc


@licenses_router.post("/renew")
async def renew_license(
    body: LicenseRenewRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().licenses.renew(
            body.model_dump(by_alias=True, exclude_none=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@licenses_router.post("/revoke")
async def revoke_license(
    body: LicenseRevokeRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().licenses.revoke(
            body.model_dump(by_alias=True, exclude_none=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@licenses_router.post("/validate")
async def validate_license(
    body: LicenseValidateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    try:
        return _svc().validator.validate(body.license_key)
    except Exception as exc:
        raise _map(exc) from exc


@licenses_router.get("/history")
async def license_history(
    organization_id: str = Query(..., alias="organizationId"),
    limit: int = Query(100, ge=1, le=500),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().licenses.history(
            actor_id=actor, organization_id=organization_id, limit=limit
        )
    except Exception as exc:
        raise _map(exc) from exc


# --- Developer platform ---


@developer_router.post("/api-keys")
async def create_api_key(
    body: ApiKeyCreateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().keys.create(
            body.model_dump(by_alias=True, exclude_none=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@developer_router.get("/api-keys")
async def list_api_keys(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().keys.list(actor_id=actor, organization_id=organization_id)
    except Exception as exc:
        raise _map(exc) from exc


@developer_router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().keys.revoke(key_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@developer_router.post("/api-keys/{key_id}/rotate")
async def rotate_api_key(
    key_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().keys.rotate(key_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@developer_router.post("/tokens")
async def create_token(
    body: TokenCreateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().tokens.create(
            body.model_dump(by_alias=True, exclude_none=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@developer_router.get("/tokens")
async def list_tokens(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().tokens.list(actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@developer_router.delete("/tokens/{token_id}")
async def revoke_token(
    token_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().tokens.revoke(token_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@developer_router.post("/webhooks")
async def register_webhook(
    body: WebhookCreateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().platform.register_webhook(
            body.model_dump(by_alias=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@developer_router.get("/webhooks")
async def list_webhooks(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().platform.list_webhooks(
            actor_id=actor, organization_id=organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@developer_router.delete("/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().platform.delete_webhook(webhook_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@developer_router.get("/webhooks/{webhook_id}/retries")
async def webhook_retries(
    webhook_id: str,
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().platform.retry_queue(
            actor_id=actor, organization_id=organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@developer_router.get("/usage")
async def developer_usage(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().platform.usage(actor_id=actor, organization_id=organization_id)
    except Exception as exc:
        raise _map(exc) from exc


@developer_router.get("/rate-limits")
async def rate_limit_status(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().rate_limits.status(
            actor_id=actor, organization_id=organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@developer_router.get("/docs")
async def developer_docs(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().platform.docs()


@developer_router.get("/status")
async def engine_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().status()
