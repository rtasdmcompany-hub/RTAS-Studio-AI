"""API for AI Avatar & Character Generation under /api/avatar."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import character_generation as cg

router = APIRouter(prefix="/avatar", tags=["avatar"])


def _require_backend_auth(x_rtas_backend_secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if not expected:
        return
    if (x_rtas_backend_secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


class AvatarCreateRequest(BaseModel):
    name: str | None = None
    prompt: str | None = None
    template_id: str | None = Field(None, alias="templateId")
    registry_slot: str | None = Field(None, alias="registrySlot")
    gender: str | None = None
    age: int | None = None
    ethnicity: str | None = None
    body_type: str | None = Field(None, alias="bodyType")
    hairstyle: str | None = None
    beard: str | None = None
    skin: str | None = None
    eye_color: str | None = Field(None, alias="eyeColor")
    clothing: str | None = None
    accessories: list[str] | None = None
    provider: str = "simulation"
    parent_generation_id: str | None = Field(None, alias="parentGenerationId")

    model_config = {"populate_by_name": True}


@router.post("/create")
async def create_avatar(
    body: AvatarCreateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        result = cg.create_character_dict(
            name=body.name,
            prompt=body.prompt,
            template_id=body.template_id,
            registry_slot=body.registry_slot,
            gender=body.gender,
            age=body.age,
            ethnicity=body.ethnicity,
            body_type=body.body_type,
            hairstyle=body.hairstyle,
            beard=body.beard,
            skin=body.skin,
            eye_color=body.eye_color,
            clothing=body.clothing,
            accessories=body.accessories,
            provider=body.provider,
            parent_generation_id=body.parent_generation_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Avatar create failed") from exc
    return {"ok": True, **result}


@router.get("/list")
async def list_avatars(
    limit: int = Query(50, ge=1, le=500),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return {"ok": True, **cg.list_characters(limit=limit)}


@router.get("/paddle-status")
async def avatar_paddle_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    """Paddle production config check — presence flags only, never secret values."""
    _require_backend_auth(x_rtas_backend_secret)
    return {"ok": True, "paddle": cg.paddle_status(), "secrets_exposed": False}


@router.get("/{avatar_id}")
async def get_avatar(
    avatar_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    payload = cg.get_avatar_payload(avatar_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Avatar not found")
    return payload
