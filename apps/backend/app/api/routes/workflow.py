"""Workflow Automation APIs."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.backend_auth import require_backend_secret
from app.core.config import settings
from app.services import workflow_pipeline as wp
from app.services.workflow_pipeline.security import WorkflowAuthError

router = APIRouter(prefix="/workflow", tags=["workflow-pipeline"])


def _require_backend_auth(x_rtas_backend_secret: str | None) -> None:
    require_backend_secret(x_rtas_backend_secret=x_rtas_backend_secret)


class WorkflowCreateRequest(BaseModel):
    user_id: str = Field(..., alias="userId", min_length=1)
    prompt: str = Field(..., min_length=1)
    project_id: str | None = Field(None, alias="projectId")
    name: str | None = None
    template_id: str | None = Field(None, alias="templateId")
    custom_stages: list[str] | None = Field(None, alias="customStages")
    auto_trigger: bool = Field(True, alias="autoTrigger")
    metadata: dict[str, Any] | None = None
    max_retries: int | None = Field(None, alias="maxRetries")

    model_config = {"populate_by_name": True}


class WorkflowIdRequest(BaseModel):
    user_id: str = Field(..., alias="userId", min_length=1)
    workflow_id: str = Field(..., alias="workflowId", min_length=1)

    model_config = {"populate_by_name": True}


@router.post("/create")
async def workflow_create(
    body: WorkflowCreateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    engine = wp.get_workflow_engine()
    try:
        return engine.create(
            user_id=body.user_id,
            prompt=body.prompt,
            project_id=body.project_id,
            name=body.name,
            template_id=body.template_id,
            custom_stages=body.custom_stages,
            auto_trigger=body.auto_trigger,
            metadata=body.metadata,
            max_retries=body.max_retries,
        )
    except WorkflowAuthError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Workflow create failed") from exc


@router.post("/start")
async def workflow_start(
    body: WorkflowIdRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    engine = wp.get_workflow_engine()
    try:
        return engine.start(user_id=body.user_id, workflow_id=body.workflow_id)
    except WorkflowAuthError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Workflow start failed") from exc


@router.post("/resume")
async def workflow_resume(
    body: WorkflowIdRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    engine = wp.get_workflow_engine()
    try:
        return engine.resume(user_id=body.user_id, workflow_id=body.workflow_id)
    except WorkflowAuthError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Workflow resume failed") from exc


@router.post("/cancel")
async def workflow_cancel(
    body: WorkflowIdRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    engine = wp.get_workflow_engine()
    try:
        return engine.cancel(user_id=body.user_id, workflow_id=body.workflow_id)
    except WorkflowAuthError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Workflow cancel failed") from exc


@router.get("/history")
async def workflow_history(
    user_id: str | None = Query(None, alias="userId"),
    limit: int = Query(50, ge=1, le=500),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    engine = wp.get_workflow_engine()
    return engine.history(user_id=user_id, limit=limit)


@router.get("/{workflow_id}")
async def workflow_get(
    workflow_id: str,
    user_id: str | None = Query(None, alias="userId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    engine = wp.get_workflow_engine()
    try:
        return engine.get(workflow_id, user_id=user_id)
    except WorkflowAuthError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Workflow get failed") from exc
