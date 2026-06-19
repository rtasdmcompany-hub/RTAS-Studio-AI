from fastapi import APIRouter

from app.core.config import settings
from app.services.fal_verify import get_startup_verify_result as get_fal_startup_verify_result
from app.services.providers.comfyui import ComfyUIProvider
from app.services.providers.diffusers_local import DiffusersInstantIDProvider
from app.services.providers.fal import FalProvider
from app.services.providers.replicate import ReplicateProvider
from app.services.model_routing import get_cost_policy_payload, get_routing_policy_summary

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/status")
async def ai_status():
    """Which AI backends are configured (no secrets exposed)."""
    fal = get_fal_startup_verify_result()
    replicate = get_replicate_startup_verify_result()
    return {
        "provider_mode": settings.ai_provider_mode,
        "storage_mode": settings.storage_mode,
        "public_base_url": settings.public_base_url,
        "primary_provider": (
            "fal"
            if settings.fal_configured
            else ("replicate" if settings.replicate_configured else "simulation")
        ),
        "fal_models": {
            "i2v": settings.fal_model_i2v,
            "t2v": settings.fal_model_t2v,
            "real_face": settings.fal_model_real_face,
            "flashhead": settings.fal_model_flashhead,
            "cinematic": settings.fal_model_cinematic,
        },
        "replicate_models": {
            "i2v": settings.replicate_model_i2v,
            "t2v": settings.replicate_model_t2v,
            "real_face": settings.replicate_model_real_face,
        },
        "fal": {
            "configured": settings.fal_configured,
            "valid": fal.valid if fal else None,
            "live_generation": fal.live_generation_enabled if fal else False,
            "live_enabled": settings.fal_live_enabled,
            "error": fal.error if fal and fal.valid is False else None,
        },
        "replicate": {
            "configured": settings.replicate_configured,
            "valid": replicate.valid if replicate else None,
            "live_generation": replicate.live_generation_enabled if replicate else False,
            "username": replicate.username if replicate and replicate.valid else None,
            "error": replicate.error if replicate and replicate.valid is False else None,
        },
        "providers": {
            "fal": FalProvider().is_configured(),
            "replicate": ReplicateProvider().is_configured(),
            "comfyui": ComfyUIProvider().is_configured(),
            "diffusers": DiffusersInstantIDProvider().is_configured(),
        },
        "paths": {
            "uploads": str(settings.local_upload_dir),
            "outputs": str(settings.local_output_dir),
        },
        "model_routing": get_routing_policy_summary(),
    }


@router.get("/cost-policy")
async def ai_cost_policy(duration_seconds: int = 30):
    """Budget cap ($0.020/s) and weighted credit deduction (1:1 → 5:1)."""
    return get_cost_policy_payload(duration_seconds)
