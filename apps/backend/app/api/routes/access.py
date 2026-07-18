"""Enterprise Authentication & Access Control APIs — Phase 7 Sprint 2."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import enterprise_auth as ea
from app.services.enterprise_auth.errors import AccessError

router = APIRouter(prefix="/access", tags=["enterprise-auth"])


def _require_backend_auth(x_rtas_backend_secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if not expected:
        return
    if (x_rtas_backend_secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _svc():
    return ea.get_enterprise_auth_service()


def _map_error(exc: Exception) -> HTTPException:
    if isinstance(exc, AccessError):
        return HTTPException(
            status_code=exc.status_code,
            detail={"error": exc.code, "message": exc.message},
        )
    return HTTPException(status_code=500, detail="Access operation failed")


class SessionCreateRequest(BaseModel):
    user_id: str = Field(..., alias="userId", min_length=1)
    organization_id: str | None = Field(None, alias="organizationId")
    workspace_id: str | None = Field(None, alias="workspaceId")
    team_id: str | None = Field(None, alias="teamId")
    auth_provider: str = Field("credentials", alias="authProvider")
    sso_provider: str | None = Field(None, alias="ssoProvider")
    metadata: dict[str, Any] | None = None

    model_config = {"populate_by_name": True}


class SessionTokenRequest(BaseModel):
    token: str = Field(..., min_length=1)
    session_id: str | None = Field(None, alias="sessionId")

    model_config = {"populate_by_name": True}


class AuthorizeRequest(BaseModel):
    user_id: str | None = Field(None, alias="userId")
    organization_id: str | None = Field(None, alias="organizationId")
    workspace_id: str | None = Field(None, alias="workspaceId")
    team_id: str | None = Field(None, alias="teamId")
    session_token: str | None = Field(None, alias="sessionToken")
    permission: str | None = None
    action: str | None = None
    require_owner: bool = Field(False, alias="requireOwner")
    ip: str | None = None

    model_config = {"populate_by_name": True}


class OrgValidateRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId", min_length=1)
    user_id: str = Field(..., alias="userId", min_length=1)
    permission: str | None = None

    model_config = {"populate_by_name": True}


class WorkspaceValidateRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId", min_length=1)
    workspace_id: str = Field(..., alias="workspaceId", min_length=1)
    user_id: str = Field(..., alias="userId", min_length=1)
    permission: str | None = "workspace.read"

    model_config = {"populate_by_name": True}


class TeamValidateRequest(BaseModel):
    team_id: str = Field(..., alias="teamId", min_length=1)
    user_id: str = Field(..., alias="userId", min_length=1)

    model_config = {"populate_by_name": True}


class OwnershipValidateRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId", min_length=1)
    user_id: str = Field(..., alias="userId", min_length=1)

    model_config = {"populate_by_name": True}


class PermissionCheckRequest(BaseModel):
    role: str | None = None
    role_key: str | None = Field(None, alias="roleKey")
    user_id: str | None = Field(None, alias="userId")
    organization_id: str | None = Field(None, alias="organizationId")
    action: str = "content.read"
    permission: str | None = None

    model_config = {"populate_by_name": True}


class InviteAcceptRequest(BaseModel):
    token: str = Field(..., min_length=1)
    user_id: str = Field(..., alias="userId", min_length=1)
    session_token: str | None = Field(None, alias="sessionToken")

    model_config = {"populate_by_name": True}


class SSOBeginRequest(BaseModel):
    provider: str = "oidc_generic"
    organization_id: str | None = Field(None, alias="organizationId")
    user_id: str | None = Field(None, alias="userId")

    model_config = {"populate_by_name": True}


@router.get("/status")
async def access_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return _svc().status()


@router.post("/session/create")
async def session_create(
    body: SessionCreateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        return _svc().create_session(body.model_dump(by_alias=True))
    except Exception as exc:
        raise _map_error(exc) from exc


@router.post("/session/validate")
async def session_validate(
    body: SessionTokenRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        return _svc().validate_session(body.token)
    except Exception as exc:
        raise _map_error(exc) from exc


@router.post("/session/revoke")
async def session_revoke(
    body: SessionTokenRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        return _svc().revoke_session(token=body.token, session_id=body.session_id)
    except Exception as exc:
        raise _map_error(exc) from exc


@router.post("/authorize")
async def authorize(
    body: AuthorizeRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        return _svc().authorize(body.model_dump(by_alias=True))
    except Exception as exc:
        raise _map_error(exc) from exc


@router.post("/org/validate")
async def org_validate(
    body: OrgValidateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        return _svc().validate_organization(body.model_dump(by_alias=True))
    except Exception as exc:
        raise _map_error(exc) from exc


@router.post("/workspace/validate")
async def workspace_validate(
    body: WorkspaceValidateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        return _svc().validate_workspace(body.model_dump(by_alias=True))
    except Exception as exc:
        raise _map_error(exc) from exc


@router.post("/team/validate")
async def team_validate(
    body: TeamValidateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        return _svc().validate_team(body.model_dump(by_alias=True))
    except Exception as exc:
        raise _map_error(exc) from exc


@router.post("/ownership/validate")
async def ownership_validate(
    body: OwnershipValidateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        return _svc().validate_ownership(body.model_dump(by_alias=True))
    except Exception as exc:
        raise _map_error(exc) from exc


@router.post("/permission/check")
async def permission_check(
    body: PermissionCheckRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        return _svc().check_permission(body.model_dump(by_alias=True))
    except Exception as exc:
        raise _map_error(exc) from exc


@router.get("/permission/catalog")
async def permission_catalog(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return _svc().permission_catalog()


@router.post("/invite/accept")
async def invite_accept(
    body: InviteAcceptRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        return _svc().accept_invite(body.model_dump(by_alias=True))
    except Exception as exc:
        raise _map_error(exc) from exc


@router.get("/audit")
async def access_audit(
    limit: int = Query(50, ge=1, le=500),
    organization_id: str | None = Query(None, alias="organizationId"),
    event_type: str | None = Query(None, alias="eventType"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return _svc().list_audits(
        limit=limit, organization_id=organization_id, event_type=event_type
    )


@router.get("/sso/providers")
async def sso_providers(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return _svc().sso_providers()


@router.post("/sso/begin")
async def sso_begin(
    body: SSOBeginRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return _svc().sso_begin(body.model_dump(by_alias=True))
