"""Analytics, Reporting & BI APIs — Phase 7 Sprint 8."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import analytics_bi as ab
from app.services.enterprise_auth.errors import AccessError
from app.services.multi_tenant.validation import ValidationError

analytics_router = APIRouter(prefix="/analytics", tags=["analytics-bi"])
reports_router = APIRouter(prefix="/reports", tags=["analytics-bi"])
kpi_router = APIRouter(prefix="/kpi", tags=["analytics-bi"])


def _auth(secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if expected and (secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _svc():
    return ab.get_analytics_bi_service()


def _map(exc: Exception) -> HTTPException:
    if isinstance(exc, AccessError):
        return HTTPException(
            status_code=exc.status_code,
            detail={"error": exc.code, "message": exc.message},
        )
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=500, detail="Analytics operation failed")


def _user(user_id: str | None) -> str:
    if not user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    return user_id


class GenerateReportRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    report_type: str = Field("daily", alias="reportType")
    scope: str = "organization"
    workspace_id: str | None = Field(None, alias="workspaceId")
    title: str | None = None
    model_config = {"populate_by_name": True}


# --- Analytics ---


@analytics_router.get("/status")
async def analytics_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().status()


@analytics_router.get("/observability")
async def analytics_observability(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().observability()


@analytics_router.get("/overview")
async def analytics_overview(
    organization_id: str = Query(..., alias="organizationId"),
    workspace_id: str | None = Query(None, alias="workspaceId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().analytics.overview(
            actor_id=actor,
            organization_id=organization_id,
            workspace_id=workspace_id,
        )
    except Exception as exc:
        raise _map(exc) from exc


@analytics_router.get("/organizations")
async def analytics_organizations(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().analytics.organizations(
            actor_id=actor, organization_id=organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@analytics_router.get("/projects")
async def analytics_projects(
    organization_id: str = Query(..., alias="organizationId"),
    workspace_id: str | None = Query(None, alias="workspaceId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().analytics.projects(
            actor_id=actor,
            organization_id=organization_id,
            workspace_id=workspace_id,
        )
    except Exception as exc:
        raise _map(exc) from exc


@analytics_router.get("/ai")
async def analytics_ai(
    organization_id: str = Query(..., alias="organizationId"),
    workspace_id: str | None = Query(None, alias="workspaceId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().analytics.ai(
            actor_id=actor,
            organization_id=organization_id,
            workspace_id=workspace_id,
        )
    except Exception as exc:
        raise _map(exc) from exc


@analytics_router.get("/storage")
async def analytics_storage(
    organization_id: str = Query(..., alias="organizationId"),
    workspace_id: str | None = Query(None, alias="workspaceId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().analytics.storage(
            actor_id=actor,
            organization_id=organization_id,
            workspace_id=workspace_id,
        )
    except Exception as exc:
        raise _map(exc) from exc


@analytics_router.get("/bi")
async def analytics_bi_insights(
    organization_id: str = Query(..., alias="organizationId"),
    workspace_id: str | None = Query(None, alias="workspaceId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().bi.insights(
            actor_id=actor,
            organization_id=organization_id,
            workspace_id=workspace_id,
        )
    except Exception as exc:
        raise _map(exc) from exc


# --- Reports ---


@reports_router.get("")
async def list_reports(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().reporting.list(actor_id=actor, organization_id=organization_id)
    except Exception as exc:
        raise _map(exc) from exc


@reports_router.post("/generate")
async def generate_report(
    body: GenerateReportRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().reporting.generate(body.model_dump(by_alias=True), actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


# --- KPI ---


@kpi_router.get("")
async def get_kpis(
    organization_id: str = Query(..., alias="organizationId"),
    workspace_id: str | None = Query(None, alias="workspaceId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().kpis.compute(
            actor_id=actor,
            organization_id=organization_id,
            workspace_id=workspace_id,
        )
    except Exception as exc:
        raise _map(exc) from exc
