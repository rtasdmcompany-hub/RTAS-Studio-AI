"""Pipeline status API."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

from app.core.config import settings
from app.services import workflow_pipeline as wp

router = APIRouter(prefix="/pipeline", tags=["workflow-pipeline"])


def _require_backend_auth(x_rtas_backend_secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if not expected:
        return
    if (x_rtas_backend_secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("/status")
async def pipeline_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    engine = wp.get_workflow_engine()
    return engine.pipeline_status()
