"""Context APIs — load / reconstruct continuity context."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import memory_knowledge as mk
from app.services.memory_knowledge.security import AccessDenied

router = APIRouter(prefix="/context", tags=["memory-knowledge"])


def _require_backend_auth(x_rtas_backend_secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if not expected:
        return
    if (x_rtas_backend_secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


class ContextLoadRequest(BaseModel):
    user_id: str = Field(..., alias="userId", min_length=1)
    project_id: str | None = Field(None, alias="projectId")
    prompt: str | None = None
    output: str | None = None
    story: dict[str, Any] | None = None
    character: dict[str, Any] | None = None
    scene: dict[str, Any] | None = None
    camera: dict[str, Any] | None = None
    audio: dict[str, Any] | None = None
    environment: dict[str, Any] | None = None
    workflow: dict[str, Any] | None = None
    memory_refs: list[str] | None = Field(None, alias="memoryRefs")

    model_config = {"populate_by_name": True}


@router.post("/load")
async def context_load(
    body: ContextLoadRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    engine = mk.get_memory_engine()
    try:
        return engine.load_context(
            user_id=body.user_id,
            project_id=body.project_id,
            prompt=body.prompt,
            output=body.output,
            story=body.story,
            character=body.character,
            scene=body.scene,
            camera=body.camera,
            audio=body.audio,
            environment=body.environment,
            workflow=body.workflow,
            memory_refs=body.memory_refs,
        )
    except AccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Context load failed") from exc
