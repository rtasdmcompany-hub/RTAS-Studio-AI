"""API for AI Voice & Dialogue Intelligence under /api/voice."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import voice_intelligence as vi
from app.services.character_generation.paddle_status import paddle_status

router = APIRouter(prefix="/voice", tags=["voice-intelligence"])


def _require_backend_auth(x_rtas_backend_secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if not expected:
        return
    if (x_rtas_backend_secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


class VoiceAnalyzeRequest(BaseModel):
    script: str = Field(..., min_length=1)
    project_id: str | None = Field(None, alias="projectId")
    language: str = "en"
    assignments: list[dict] | None = None

    model_config = {"populate_by_name": True}


class VoiceAssignRequest(BaseModel):
    project_id: str = Field(..., alias="projectId")
    language: str | None = None
    assignments: list[dict] | None = None

    model_config = {"populate_by_name": True}


class VoiceSynchronizeRequest(BaseModel):
    project_id: str = Field(..., alias="projectId")

    model_config = {"populate_by_name": True}


@router.post("/analyze")
async def analyze_voice_script(
    body: VoiceAnalyzeRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        result = vi.analyze_dict(
            script=body.script,
            project_id=body.project_id,
            language=body.language,
            assignments=body.assignments,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Voice analyze failed") from exc
    return {"ok": True, **result}


@router.post("/assign")
async def assign_voice_profiles(
    body: VoiceAssignRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        result = vi.assign_dict(
            project_id=body.project_id,
            assignments=body.assignments,
            language=body.language,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Voice assign failed") from exc
    return {"ok": True, **result}


@router.post("/synchronize")
async def synchronize_voice_project(
    body: VoiceSynchronizeRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        result = vi.synchronize_dict(project_id=body.project_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Voice synchronize failed") from exc
    return {"ok": True, **result}


@router.get("/paddle-status")
async def voice_paddle_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    """Paddle presence flags only — never secret values."""
    _require_backend_auth(x_rtas_backend_secret)
    return {"ok": True, "paddle": paddle_status(), "secrets_exposed": False}


@router.get("/{project_id}")
async def get_voice_project(
    project_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    payload = vi.get_project(project_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Voice project not found")
    return {"ok": True, **payload}
