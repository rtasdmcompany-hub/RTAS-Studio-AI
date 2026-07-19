"""AI Agents, Automation Workflows & Orchestration APIs — Phase 9 Sprint 7."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import agent_orchestration as ao_svc
from app.services.enterprise_auth.errors import AccessError
from app.services.multi_tenant.validation import ValidationError

agents_router = APIRouter(prefix="/agents", tags=["agents"])
workflows_router = APIRouter(prefix="/workflows", tags=["workflows"])


def _auth(secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if expected and (secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _svc():
    return ao_svc.get_agent_orchestration_service()


def _map(exc: Exception) -> HTTPException:
    if isinstance(exc, AccessError):
        return HTTPException(
            status_code=exc.status_code,
            detail={"error": exc.code, "message": exc.message},
        )
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(
        status_code=500, detail="Agent orchestration operation failed"
    )


def _user(user_id: str | None) -> str:
    if not user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    return user_id


class AgentCreateRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    name: str
    agent_type: str = Field("custom", alias="agentType")
    description: str = ""
    workspace_id: str | None = Field(None, alias="workspaceId")
    capabilities: list[str] | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    model_config = {"populate_by_name": True}


class AgentUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    config: dict[str, Any] | None = None
    model_config = {"populate_by_name": True}


class WorkflowCreateRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    name: str
    description: str = ""
    trigger: str = "manual"
    mode: str = "sequential"
    workspace_id: str | None = Field(None, alias="workspaceId")
    steps: list[dict[str, Any]] = Field(default_factory=list)
    conditions: dict[str, Any] = Field(default_factory=dict)
    template_slug: str | None = Field(None, alias="templateSlug")
    model_config = {"populate_by_name": True}


class WorkflowRunRequest(BaseModel):
    workflow_id: str = Field(..., alias="workflowId")
    trigger: str = "manual"
    context: dict[str, Any] = Field(default_factory=dict)
    priority: str = "normal"
    max_retries: int | None = Field(None, alias="maxRetries")
    workspace_id: str | None = Field(None, alias="workspaceId")
    model_config = {"populate_by_name": True}


class ScheduleRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    workflow_id: str = Field(..., alias="workflowId")
    kind: str = "once"
    priority: str = "normal"
    cron: str = ""
    delay_minutes: int = Field(0, alias="delayMinutes")
    interval_hours: int = Field(1, alias="intervalHours")
    max_retries: int | None = Field(None, alias="maxRetries")
    model_config = {"populate_by_name": True}


class CollaborateRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    agent_ids: list[str] = Field(..., alias="agentIds")
    task: str
    model_config = {"populate_by_name": True}


# --- Agents (static routes before /{id}) ---


@agents_router.get("/status")
async def agents_status(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().agents.status_summary(
            actor_id=actor, organization_id=organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@agents_router.post("/create")
async def create_agent(
    body: AgentCreateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().agents.create(body.model_dump(by_alias=True), actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@agents_router.get("")
async def list_agents(
    organization_id: str = Query(..., alias="organizationId"),
    workspace_id: str | None = Query(None, alias="workspaceId"),
    agent_type: str | None = Query(None, alias="agentType"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().agents.list(
            actor_id=actor,
            organization_id=organization_id,
            workspace_id=workspace_id,
            agent_type=agent_type,
        )
    except Exception as exc:
        raise _map(exc) from exc


@agents_router.post("/collaborate")
async def collaborate_agents(
    body: CollaborateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().orchestrator.collaborate(
            body.model_dump(by_alias=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@agents_router.get("/{agent_id}")
async def get_agent(
    agent_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().agents.get(agent_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@agents_router.patch("/{agent_id}")
async def update_agent(
    agent_id: str,
    body: AgentUpdateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().agents.update(
            agent_id,
            body.model_dump(by_alias=True, exclude_unset=True),
            actor_id=actor,
        )
    except Exception as exc:
        raise _map(exc) from exc


@agents_router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().agents.delete(agent_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@agents_router.get("/{agent_id}/memory")
async def list_agent_memory(
    agent_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().memory.list(agent_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


# --- Workflows ---


@workflows_router.get("/templates")
async def list_workflow_templates():
    return _svc().workflows.list_templates()


@workflows_router.post("/create")
async def create_workflow(
    body: WorkflowCreateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().workflows.create(
            body.model_dump(by_alias=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@workflows_router.post("/run")
async def run_workflow(
    body: WorkflowRunRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().execution.run(body.model_dump(by_alias=True), actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@workflows_router.get("/history")
async def workflow_history(
    organization_id: str = Query(..., alias="organizationId"),
    workflow_id: str | None = Query(None, alias="workflowId"),
    limit: int = Query(50, ge=1, le=500),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().execution.history(
            actor_id=actor,
            organization_id=organization_id,
            workflow_id=workflow_id,
            limit=limit,
        )
    except Exception as exc:
        raise _map(exc) from exc


@workflows_router.post("/schedule")
async def schedule_workflow(
    body: ScheduleRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().scheduler.schedule(
            body.model_dump(by_alias=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@workflows_router.get("/jobs")
async def list_scheduled_jobs(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().scheduler.list(
            actor_id=actor, organization_id=organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@workflows_router.get("/engine-status")
async def orchestration_engine_status():
    return _svc().status()
