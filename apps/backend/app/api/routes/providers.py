"""API for Multi AI Provider Orchestration under /api/providers."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import provider_connectors as pc
from app.services import provider_orchestration as po

router = APIRouter(prefix="/providers", tags=["provider-orchestration"])


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


@router.get("")
@router.get("/")
async def list_providers_root(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    """Installed providers — status, supported capabilities, version."""
    _require_backend_auth(x_rtas_backend_secret)
    manager = po.get_provider_manager()
    manager.discover()
    payload = manager.list_installed()
    health = await manager.health_monitor()
    # Enrich status from latest health probe
    by_id = {r["provider_id"]: r for r in health.get("reports") or []}
    providers = []
    for item in payload.get("installed_providers") or []:
        h = by_id.get(item["provider_id"]) or {}
        providers.append(
            {
                **item,
                "status": h.get("status") or item.get("status"),
                "supported_capabilities": item.get("capabilities") or [],
                "version": item.get("version"),
                "health_latency_ms": h.get("latency_ms"),
            }
        )
    return {
        "ok": True,
        "engine": payload.get("engine"),
        "version": payload.get("version"),
        "label": payload.get("label"),
        "installed_providers": providers,
        "count": len(providers),
        "priority_order": payload.get("priority_order"),
        "capabilities_catalog": payload.get("capabilities_catalog"),
        "status_catalog": payload.get("status_catalog"),
        "health": {
            "online": health.get("online"),
            "total": health.get("total"),
            "all_healthy": health.get("all_healthy"),
        },
    }


@router.get("/list")
async def list_providers_connectors(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    """Connector framework list (Sprint 2 compatibility)."""
    _require_backend_auth(x_rtas_backend_secret)
    engine = pc.get_connector_engine()
    return {"ok": True, **engine.list_providers()}


@router.get("/status")
async def providers_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    manager = po.get_provider_manager()
    health = await manager.health_monitor()
    return {
        "ok": True,
        "engine": po.ENGINE_NAME,
        "version": po.ENGINE_VERSION,
        **health,
    }


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
