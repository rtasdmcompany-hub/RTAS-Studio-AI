from fastapi import APIRouter

from app.core.config import reload_settings, settings
from app.services.fal_guard import clear_billing_block_if_fal_valid, get_guard_public_status
from app.services.fal_verify import get_startup_verify_result, verify_fal_key
from app.services.replicate_verify import (
    get_startup_verify_result as get_replicate_startup_result,
    verify_replicate_token,
)

router = APIRouter(tags=["health"])


@router.get("/health/ping")
async def health_ping():
    """Fast liveness probe (no external provider round-trips)."""
    reload_settings()
    return {
        "status": "healthy",
        "service": "rtas-studio-ai-api",
        "fal": {"configured": settings.fal_configured},
        "replicate": {"configured": settings.replicate_configured},
    }


@router.get("/ready")
async def ready():
    """Production readiness probe — Phase 7 multi-tenant SaaS platform."""
    reload_settings()
    return {
        "status": "ready",
        "ok": True,
        "service": "rtas-studio-ai-api",
        "version": "1.0.0",
        "phase": 7,
        "sprint": 7,
        "final_release": True,
        "platform": "RTAS Studio AI Enterprise SaaS Platform",
        "management_engine": "RTAS Organization, Workspace & Team Management Engine v1.0",
        "project_engine": "RTAS Project Management & Collaboration Engine v1.0",
        "asset_engine": "RTAS Enterprise Asset Management & Digital Library Engine v1.0",
        "notification_engine": "RTAS Enterprise Notifications, Comments & Activity Engine v1.0",
        "version_engine": "RTAS Enterprise Version Control, Approval & Review Engine v1.0",
        "director_engine": "RTAS Studio AI Director Engine v1.0",
    }


@router.get("/health")
async def health():
    reload_settings()
    guard = get_guard_public_status()

    # Re-check Fal when guard is blocked or startup cache is missing — billing top-ups
    # do not clear fal-guard.json automatically until we verify the key again.
    fal = get_startup_verify_result()
    if settings.fal_configured and (
        guard.get("billing_blocked") or fal is None or fal.valid is False
    ):
        fal = await verify_fal_key()
        if guard.get("billing_blocked") and fal.valid:
            clear_billing_block_if_fal_valid(True)
            guard = get_guard_public_status()

    replicate = get_replicate_startup_result()
    if replicate is None and settings.replicate_configured:
        replicate = await verify_replicate_token()

    return {
        "status": "healthy",
        "service": "rtas-studio-ai-api",
        "version": "1.0.0",
        "ai_provider_mode": settings.ai_provider_mode,
        "primary_provider": "fal" if settings.fal_configured else (
            "replicate" if settings.replicate_configured else "simulation"
        ),
        "fal": {
            "configured": settings.fal_configured,
            "valid": fal.valid if fal else None,
            "live_generation": (
                fal.live_generation_enabled
                if fal
                else False
            ) and guard.get("live_calls_allowed", True),
            "live_enabled": settings.fal_live_enabled,
            "guard": guard,
            "error": fal.error if fal and fal.valid is False else None,
        },
        "replicate": {
            "configured": settings.replicate_configured,
            "valid": replicate.valid if replicate else None,
            "live_generation": replicate.live_generation_enabled if replicate else False,
            "username": replicate.username if replicate and replicate.valid else None,
            "error": replicate.error if replicate and replicate.valid is False else None,
        },
    }
