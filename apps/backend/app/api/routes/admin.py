"""Owner-only maintenance endpoints."""

from fastapi import APIRouter, Header

from app.core.backend_auth import require_backend_secret
from app.core.config import reload_settings
from app.services.fal_guard import get_guard_public_status, reset_guard
from app.services.fal_verify import verify_fal_key

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_owner_secret(x_rtas_admin_secret: str | None) -> None:
    """Admin mutations use the same fail-closed secret policy as backend auth."""
    reload_settings()
    require_backend_secret(x_rtas_backend_secret=x_rtas_admin_secret)


@router.get("/fal/guard")
async def fal_guard_status():
    """Public read — studio UI can show why live Fal is paused."""
    return get_guard_public_status()


@router.post("/fal/reset-guard")
async def fal_reset_guard(
    x_rtas_admin_secret: str | None = Header(default=None),
):
    """
    Owner resets Fal guard after topping up billing.
    Set AI_BACKEND_SECRET in apps/backend/.env and pass header X-Rtas-Admin-Secret.
    """
    _require_owner_secret(x_rtas_admin_secret)
    status = reset_guard()
    verify = await verify_fal_key()
    status["fal_valid_after_reset"] = verify.valid
    status["fal_error_after_reset"] = verify.error
    return {"ok": True, "guard": status}
