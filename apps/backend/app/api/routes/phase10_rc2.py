"""Phase 10 Sprint 9 — Production Environment & RC-2 APIs."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

from app.core.config import settings
from app.services import phase10_production as prod_svc

router = APIRouter(prefix="/phase10/rc2", tags=["phase10-rc2"])


def _auth(secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if expected and (secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _svc():
    return prod_svc.get_phase10_production_service()


@router.get("/status")
async def rc2_status():
    return _svc().status()


@router.get("/environment")
async def rc2_environment(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().production_environment_audit()


@router.get("/inventory")
async def rc2_inventory(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().environment_inventory()


@router.get("/secret-rotation-plan")
async def rc2_secret_rotation_plan(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().secret_rotation_plan()


@router.get("/deployment")
async def rc2_deployment(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().deployment_pipeline_audit()


@router.post("/validate")
async def rc2_validate(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().run_rc2_validation()


@router.post("/smoke")
async def rc2_smoke(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().production_smoke_tests()


@router.get("/launch-checklist")
async def rc2_launch_checklist(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().final_launch_checklist()


@router.get("/report")
async def rc2_report(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().full_report()
