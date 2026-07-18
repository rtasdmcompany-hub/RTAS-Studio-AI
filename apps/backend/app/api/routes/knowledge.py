"""Knowledge APIs — searchable knowledge base."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Header, HTTPException, Query

from app.core.config import settings
from app.services import memory_knowledge as mk
from app.services.memory_knowledge.security import AccessDenied

router = APIRouter(prefix="/knowledge", tags=["memory-knowledge"])

KnowledgeKindLit = Literal[
    "project",
    "character",
    "scene",
    "asset",
    "prompt",
    "template",
    "style",
    "preset",
    "production_report",
]


def _require_backend_auth(x_rtas_backend_secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if not expected:
        return
    if (x_rtas_backend_secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("/search")
async def knowledge_search(
    query: str = Query(..., min_length=1),
    user_id: str = Query(..., alias="userId"),
    kind: KnowledgeKindLit | None = Query(None),
    project_id: str | None = Query(None, alias="projectId"),
    top_k: int = Query(20, alias="topK", ge=1, le=100),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    engine = mk.get_memory_engine()
    try:
        return engine.knowledge_search(
            user_id=user_id,
            query=query,
            kind=kind,
            project_id=project_id,
            top_k=top_k,
        )
    except AccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Knowledge search failed") from exc
