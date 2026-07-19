"""Enterprise Automation, Event Bus & Integration Hub APIs — Phase 9 Sprint 8."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import enterprise_automation as ea_svc
from app.services.enterprise_auth.errors import AccessError
from app.services.multi_tenant.validation import ValidationError

automation_router = APIRouter(prefix="/automation", tags=["automation"])
events_router = APIRouter(prefix="/events", tags=["events"])
# Registered before plugin_framework integrations so POST /connect hits this hub.
integrations_hub_router = APIRouter(prefix="/integrations", tags=["integration-hub"])


def _auth(secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if expected and (secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _svc():
    return ea_svc.get_enterprise_automation_service()


def _map(exc: Exception) -> HTTPException:
    if isinstance(exc, AccessError):
        return HTTPException(
            status_code=exc.status_code,
            detail={"error": exc.code, "message": exc.message},
        )
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(
        status_code=500, detail="Enterprise automation operation failed"
    )


def _user(user_id: str | None) -> str:
    if not user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    return user_id


class AutomationCreateRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    name: str
    mode: str = "event"
    description: str = ""
    trigger_event: str = Field("", alias="triggerEvent")
    conditions: dict[str, Any] = Field(default_factory=dict)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    workspace_id: str | None = Field(None, alias="workspaceId")
    integration_id: str | None = Field(None, alias="integrationId")
    priority: int = 100
    model_config = {"populate_by_name": True}


class AutomationUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    actions: list[dict[str, Any]] | None = None
    conditions: dict[str, Any] | None = None
    priority: int | None = None
    model_config = {"populate_by_name": True}


class EventPublishRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    event_type: str = Field(..., alias="eventType")
    workspace_id: str | None = Field(None, alias="workspaceId")
    payload: dict[str, Any] = Field(default_factory=dict)
    signature: str = ""
    signing_secret: str = Field("", alias="signingSecret")
    model_config = {"populate_by_name": True}


class IntegrationConnectRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    provider: str
    workspace_id: str | None = Field(None, alias="workspaceId")
    display_name: str = Field("", alias="displayName")
    credentials_ref: str = Field("", alias="credentialsRef")
    webhook_secret: str = Field("", alias="webhookSecret")
    metadata: dict[str, Any] = Field(default_factory=dict)
    model_config = {"populate_by_name": True}


# --- Automation ---


@automation_router.get("")
async def automation_root():
    return _svc().status()


@automation_router.get("/engine-status")
async def automation_engine_status():
    return _svc().status()


@automation_router.post("/create")
async def create_automation(
    body: AutomationCreateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().automation.create(
            body.model_dump(by_alias=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@automation_router.get("")
async def list_automations(
    organization_id: str = Query(..., alias="organizationId"),
    workspace_id: str | None = Query(None, alias="workspaceId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().automation.list(
            actor_id=actor,
            organization_id=organization_id,
            workspace_id=workspace_id,
        )
    except Exception as exc:
        raise _map(exc) from exc


@automation_router.patch("/{automation_id}")
async def update_automation(
    automation_id: str,
    body: AutomationUpdateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().automation.update(
            automation_id,
            body.model_dump(by_alias=True, exclude_unset=True),
            actor_id=actor,
        )
    except Exception as exc:
        raise _map(exc) from exc


@automation_router.delete("/{automation_id}")
async def delete_automation(
    automation_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().automation.delete(automation_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


# --- Events ---


@events_router.post("/publish")
async def publish_event(
    body: EventPublishRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().publish_and_process(
            body.model_dump(by_alias=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@events_router.get("/history")
async def events_history(
    organization_id: str = Query(..., alias="organizationId"),
    event_type: str | None = Query(None, alias="eventType"),
    category: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().bus.history(
            actor_id=actor,
            organization_id=organization_id,
            event_type=event_type,
            category=category,
            limit=limit,
        )
    except Exception as exc:
        raise _map(exc) from exc


# --- Integrations hub ---


@integrations_hub_router.post("/connect")
async def connect_integration(
    body: IntegrationConnectRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().hub.connect(body.model_dump(by_alias=True), actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@integrations_hub_router.get("/status")
async def integrations_status(
    organization_id: str = Query(..., alias="organizationId"),
    workspace_id: str | None = Query(None, alias="workspaceId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().hub.status(
            actor_id=actor,
            organization_id=organization_id,
            workspace_id=workspace_id,
        )
    except Exception as exc:
        raise _map(exc) from exc
