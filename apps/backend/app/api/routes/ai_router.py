"""API for AI Model Routing Engine under /api/router."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import model_routing as mr

router = APIRouter(prefix="/router", tags=["model-routing"])


def _require_backend_auth(x_rtas_backend_secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if not expected:
        return
    if (x_rtas_backend_secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


class RouterPlanRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    request_type: str | None = Field(None, alias="requestType")
    strategy: str = "balanced"
    prefer_cheap: bool | None = Field(None, alias="preferCheap")
    provider_hint: str | None = Field(None, alias="providerHint")
    failover: bool = True
    load_balance: bool = Field(True, alias="loadBalance")

    model_config = {"populate_by_name": True}


class RouterSelectRequest(RouterPlanRequest):
    pass


@router.post("/plan")
async def plan_route(
    body: RouterPlanRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        result = mr.plan_dict(
            prompt=body.prompt,
            request_type=body.request_type,
            strategy=body.strategy,
            prefer_cheap=body.prefer_cheap,
            provider_hint=body.provider_hint,
            failover=body.failover,
            load_balance=body.load_balance,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Router plan failed") from exc
    return {"ok": True, **result}


@router.post("/select")
async def select_route(
    body: RouterSelectRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        result = mr.select_dict(
            prompt=body.prompt,
            request_type=body.request_type,
            strategy=body.strategy,
            prefer_cheap=body.prefer_cheap,
            provider_hint=body.provider_hint,
            failover=body.failover,
            load_balance=body.load_balance,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Router select failed") from exc
    return {"ok": True, **result}


@router.get("/models")
async def get_models(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return {"ok": True, **mr.list_models()}


@router.get("/status")
async def get_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return {"ok": True, **mr.router_status()}
