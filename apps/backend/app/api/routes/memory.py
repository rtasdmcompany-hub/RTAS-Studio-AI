"""Memory APIs — store, retrieve, project, history."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import memory_knowledge as mk
from app.services.memory_knowledge.security import AccessDenied

router = APIRouter(prefix="/memory", tags=["memory-knowledge"])

MemoryTypeLit = Literal[
    "short_term",
    "long_term",
    "project",
    "character",
    "scene",
    "story",
    "user_preferences",
    "production_history",
    "asset_references",
    "ai_decision_history",
    "prompt",
    "conversation",
    "user",
    "asset",
]


def _require_backend_auth(x_rtas_backend_secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if not expected:
        return
    if (x_rtas_backend_secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


class MemoryStoreRequest(BaseModel):
    user_id: str = Field(..., alias="userId", min_length=1)
    memory_type: MemoryTypeLit = Field("long_term", alias="memoryType")
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    project_id: str | None = Field(None, alias="projectId")
    character_id: str | None = Field(None, alias="characterId")
    scene_id: str | None = Field(None, alias="sceneId")
    asset_id: str | None = Field(None, alias="assetId")
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None
    importance: float = 0.5
    index_knowledge: bool = Field(True, alias="indexKnowledge")

    model_config = {"populate_by_name": True}


class MemoryRetrieveRequest(BaseModel):
    user_id: str = Field(..., alias="userId", min_length=1)
    query: str | None = None
    project_id: str | None = Field(None, alias="projectId")
    memory_type: MemoryTypeLit | None = Field(None, alias="memoryType")
    character_id: str | None = Field(None, alias="characterId")
    limit: int = 20

    model_config = {"populate_by_name": True}


@router.post("/store")
async def memory_store(
    body: MemoryStoreRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    engine = mk.get_memory_engine()
    try:
        return engine.store(
            user_id=body.user_id,
            memory_type=body.memory_type,
            title=body.title,
            content=body.content,
            project_id=body.project_id,
            character_id=body.character_id,
            scene_id=body.scene_id,
            asset_id=body.asset_id,
            tags=body.tags,
            metadata=body.metadata,
            importance=body.importance,
            index_knowledge=body.index_knowledge,
        )
    except AccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Memory store failed") from exc


@router.post("/retrieve")
async def memory_retrieve(
    body: MemoryRetrieveRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    engine = mk.get_memory_engine()
    try:
        return engine.retrieve(
            user_id=body.user_id,
            query=body.query,
            project_id=body.project_id,
            memory_type=body.memory_type,
            character_id=body.character_id,
            limit=body.limit,
        )
    except AccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Memory retrieve failed") from exc


@router.get("/project/{project_id}")
async def memory_project(
    project_id: str,
    user_id: str = Query(..., alias="userId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    engine = mk.get_memory_engine()
    try:
        return engine.project(user_id, project_id)
    except AccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Project memory failed") from exc


@router.get("/history")
async def memory_history(
    user_id: str = Query(..., alias="userId"),
    project_id: str | None = Query(None, alias="projectId"),
    limit: int = Query(50, ge=1, le=500),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    engine = mk.get_memory_engine()
    try:
        return engine.history(user_id=user_id, project_id=project_id, limit=limit)
    except AccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Memory history failed") from exc
