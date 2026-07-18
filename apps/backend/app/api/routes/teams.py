"""Team Management APIs — Phase 7 Sprint 3."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import org_management as om
from app.services.multi_tenant.validation import ValidationError
from app.services.org_management.security import AccessError

router = APIRouter(prefix="/teams", tags=["team-management"])


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
    return HTTPException(status_code=500, detail="Team operation failed")


class CreateTeamRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    name: str
    slug: str | None = None
    workspace_id: str | None = Field(None, alias="workspaceId")
    model_config = {"populate_by_name": True}


class UpdateTeamRequest(BaseModel):
    name: str | None = None
    slug: str | None = None
    status: str | None = None


class AssignMemberRequest(BaseModel):
    user_id: str = Field(..., alias="userId")
    team_role: str = Field("member", alias="teamRole")
    model_config = {"populate_by_name": True}


@router.get("/status")
async def team_engine_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    status = _svc().status()
    return {
        "ok": True,
        "engine": "team",
        "status": status["engines"]["team"],
        "phase": status["phase"],
        "sprint": status["sprint"],
        "roles": _svc().teams.roles(),
    }


@router.get("/roles")
async def team_roles(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().teams.roles()


@router.post("")
async def create_team(
    body: CreateTeamRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    if not x_rtas_user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    try:
        return _svc().teams.create(body.model_dump(by_alias=True), actor_id=x_rtas_user_id)
    except Exception as exc:
        raise _map(exc) from exc


@router.get("")
async def list_teams(
    organization_id: str = Query(..., alias="organizationId"),
    workspace_id: str | None = Query(None, alias="workspaceId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    try:
        return _svc().teams.list(
            organization_id, actor_id=x_rtas_user_id, workspace_id=workspace_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@router.patch("/{team_id}")
async def update_team(
    team_id: str,
    body: UpdateTeamRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    if not x_rtas_user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    try:
        return _svc().teams.update(
            team_id, body.model_dump(exclude_none=True), actor_id=x_rtas_user_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@router.delete("/{team_id}")
async def delete_team(
    team_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    if not x_rtas_user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    try:
        return _svc().teams.delete(team_id, actor_id=x_rtas_user_id)
    except Exception as exc:
        raise _map(exc) from exc


@router.post("/{team_id}/members")
async def assign_team_member(
    team_id: str,
    body: AssignMemberRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    if not x_rtas_user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    try:
        return _svc().teams.assign_member(
            team_id,
            body.user_id,
            actor_id=x_rtas_user_id,
            team_role=body.team_role,
        )
    except Exception as exc:
        raise _map(exc) from exc


@router.delete("/{team_id}/members/{user_id}")
async def remove_team_member(
    team_id: str,
    user_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    if not x_rtas_user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    try:
        return _svc().teams.remove_member(team_id, user_id, actor_id=x_rtas_user_id)
    except Exception as exc:
        raise _map(exc) from exc
