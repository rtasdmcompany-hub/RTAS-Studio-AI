"""API for AI Provider Connector Framework under /api/providers."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import provider_connectors as pc

router = APIRouter(prefix="/providers", tags=["provider-connectors"])


def _require_backend_auth(x_rtas_backend_secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if not expected:
        return
    if (x_rtas_backend_secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


class ProviderTestRequest(BaseModel):
    provider_id: str | None = Field(None, alias="providerId")
    prompt: str = "RTAS connector health probe"
    capability: str = "text"
    test_all: bool = Field(False, alias="testAll")

    model_config = {"populate_by_name": True}


@router.get("/list")
async def list_providers(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    engine = pc.get_connector_engine()
    return {"ok": True, **engine.list_providers()}


@router.get("/status")
async def providers_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    engine = pc.get_connector_engine()
    return {"ok": True, **await engine.status()}


@router.post("/test")
async def test_provider(
    body: ProviderTestRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    engine = pc.get_connector_engine()
    try:
        if body.test_all or not body.provider_id:
            result = await engine.test_all(prompt=body.prompt)
        else:
            result = await engine.test_provider(
                body.provider_id,
                prompt=body.prompt,
                capability=body.capability,  # type: ignore[arg-type]
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Provider test failed") from exc
    return {"ok": True, **result}


@router.get("")
@router.get("/")
async def providers_root(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    """Installed providers summary (status, capabilities, version)."""
    _require_backend_auth(x_rtas_backend_secret)
    engine = pc.get_connector_engine()
    listed = engine.list_providers()
    return {
        "ok": True,
        "installed_providers": listed.get("providers"),
        "count": listed.get("count"),
        "version": listed.get("version"),
        "engine": listed.get("engine"),
    }
