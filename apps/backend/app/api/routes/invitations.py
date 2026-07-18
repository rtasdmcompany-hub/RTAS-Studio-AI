"""Invitation Manager APIs — Phase 7 Sprint 3."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import org_management as om
from app.services.multi_tenant.validation import ValidationError
from app.services.org_management.security import AccessError

router = APIRouter(prefix="/invitations", tags=["invitation-manager"])


def _auth(secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if expected and (secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _svc():
    return om.get_org_management_service()


def _map(exc: Exception) -> HTTPException:
    if isinstance(exc, AccessError):
        return HTTPException(
            status_code=exc.status_code,
            detail={"error": exc.code, "message": exc.message},
        )
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=500, detail="Invitation operation failed")


class CreateInvitationRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    email: str
    invited_by_id: str = Field(..., alias="invitedById")
    role: str = "viewer"
    workspace_id: str | None = Field(None, alias="workspaceId")
    model_config = {"populate_by_name": True}


class AcceptInvitationRequest(BaseModel):
    token: str
    user_id: str = Field(..., alias="userId")
    model_config = {"populate_by_name": True}


class RejectInvitationRequest(BaseModel):
    token: str


@router.post("")
async def create_invitation(
    body: CreateInvitationRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    try:
        return _svc().invitations.create(
            body.model_dump(by_alias=True),
            actor_id=x_rtas_user_id or body.invited_by_id,
        )
    except Exception as exc:
        raise _map(exc) from exc


@router.post("/accept")
async def accept_invitation(
    body: AcceptInvitationRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    try:
        return _svc().invitations.accept(body.token, body.user_id)
    except Exception as exc:
        raise _map(exc) from exc


@router.post("/reject")
async def reject_invitation(
    body: RejectInvitationRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    try:
        return _svc().invitations.reject(body.token, actor_id=x_rtas_user_id)
    except Exception as exc:
        raise _map(exc) from exc
