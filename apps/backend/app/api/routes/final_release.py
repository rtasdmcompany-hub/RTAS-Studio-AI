"""API for Phase 5 Sprint 10 Final Production Release under /api/final-release."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.backend_auth import require_backend_secret
from app.core.config import settings
from app.services import final_release as fr

router = APIRouter(prefix="/final-release", tags=["final-release"])


def _require_backend_auth(x_rtas_backend_secret: str | None) -> None:
    require_backend_secret(x_rtas_backend_secret=x_rtas_backend_secret)


class VerifyRequest(BaseModel):
    prompt: str = Field(
        "Cinematic final release — hero faces conflict then finds hope at golden hour.",
        min_length=1,
    )
    project_id: str | None = Field(None, alias="projectId")
    format_type: str | None = Field(None, alias="formatType")
    genre: str | None = None
    include_export: bool = Field(True, alias="includeExport")

    model_config = {"populate_by_name": True}


class StressRequest(BaseModel):
    batches: list[int] | None = None
    max_jobs: int | None = Field(None, alias="maxJobs")

    model_config = {"populate_by_name": True}


@router.post("/verify")
async def verify_final_release(
    body: VerifyRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        result = fr.verify_dict(
            prompt=body.prompt,
            project_id=body.project_id,
            format_type=body.format_type,
            genre=body.genre,
            include_export=body.include_export,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Final release verify failed") from exc
    return {"ok": True, **result}


@router.post("/stress")
async def stress_final_release(
    body: StressRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        result = fr.stress_dict(batches=body.batches, max_jobs=body.max_jobs)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Final release stress failed") from exc
    return {"ok": True, **result}


@router.get("/report")
async def get_final_report(
    run_stress: bool = Query(False, alias="runStress"),
    stress_max_jobs: int | None = Query(25, alias="stressMaxJobs"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        result = fr.report_dict(run_stress=run_stress, stress_max_jobs=stress_max_jobs)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Final release report failed") from exc
    return {"ok": True, **result}
