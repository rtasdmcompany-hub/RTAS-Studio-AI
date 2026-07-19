"""API for AI Avatar & Character Generation under /api/avatar."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.backend_auth import require_backend_secret
from app.core.config import settings
from app.services import appearance as ap
from app.services import character_generation as cg
from app.services import face_lock as fl

router = APIRouter(prefix="/avatar", tags=["avatar"])


def _require_backend_auth(x_rtas_backend_secret: str | None) -> None:
    require_backend_secret(x_rtas_backend_secret=x_rtas_backend_secret)


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


class AvatarLockRequest(BaseModel):
    character_id: str = Field(..., alias="characterId")
    reference_url: str | None = Field(None, alias="referenceUrl")
    reference_kind: str | None = Field(None, alias="referenceKind")
    regenerate_embedding: bool = Field(False, alias="regenerateEmbedding")
    identity_strength: float = Field(0.95, alias="identityStrength")
    face_structure: str | None = Field(None, alias="faceStructure")
    eye_shape: str | None = Field(None, alias="eyeShape")
    nose: str | None = None
    lips: str | None = None
    jawline: str | None = None
    ears: str | None = None
    hairstyle: str | None = None
    beard: str | None = None
    age: int | None = None
    skin_tone: str | None = Field(None, alias="skinTone")
    body_proportions: str | None = Field(None, alias="bodyProportions")

    model_config = {"populate_by_name": True}


class AvatarVerifyRequest(BaseModel):
    character_id: str = Field(..., alias="characterId")
    candidate_reference_url: str | None = Field(None, alias="candidateReferenceUrl")
    face_structure: str | None = Field(None, alias="faceStructure")
    eye_shape: str | None = Field(None, alias="eyeShape")
    nose: str | None = None
    lips: str | None = None
    jawline: str | None = None
    ears: str | None = None
    hairstyle: str | None = None
    beard: str | None = None
    age: int | None = None
    skin_tone: str | None = Field(None, alias="skinTone")
    body_proportions: str | None = Field(None, alias="bodyProportions")

    model_config = {"populate_by_name": True}


class AvatarStyleRequest(BaseModel):
    character_id: str = Field(..., alias="characterId")
    style_preset: str | None = Field(None, alias="stylePreset")
    hairstyle: str | None = None
    hair_color: str | None = Field(None, alias="hairColor")
    beard_style: str | None = Field(None, alias="beardStyle")
    eye_color: str | None = Field(None, alias="eyeColor")
    skin_tone: str | None = Field(None, alias="skinTone")
    body_type: str | None = Field(None, alias="bodyType")
    height: str | None = None
    clothing_style: str | None = Field(None, alias="clothingStyle")
    shoes: str | None = None
    accessories: list[str] | None = None

    model_config = {"populate_by_name": True}


class AvatarOutfitRequest(BaseModel):
    character_id: str = Field(..., alias="characterId")
    outfit_id: str | None = Field(None, alias="outfitId")
    category: str | None = None
    custom_name: str | None = Field(None, alias="customName")
    clothing_style: str | None = Field(None, alias="clothingStyle")
    shoes: str | None = None
    accessories: list[str] | None = None

    model_config = {"populate_by_name": True}


def _feature_overrides(body: AvatarLockRequest | AvatarVerifyRequest) -> dict:
    raw = {
        "face_structure": body.face_structure,
        "eye_shape": body.eye_shape,
        "nose": body.nose,
        "lips": body.lips,
        "jawline": body.jawline,
        "ears": body.ears,
        "hairstyle": body.hairstyle,
        "beard": body.beard,
        "age": body.age,
        "skin_tone": body.skin_tone,
        "body_proportions": body.body_proportions,
    }
    return {k: v for k, v in raw.items() if v is not None}


def _style_overrides(body: AvatarStyleRequest) -> dict:
    raw = {
        "hairstyle": body.hairstyle,
        "hair_color": body.hair_color,
        "beard_style": body.beard_style,
        "eye_color": body.eye_color,
        "skin_tone": body.skin_tone,
        "body_type": body.body_type,
        "height": body.height,
        "clothing_style": body.clothing_style,
        "shoes": body.shoes,
        "accessories": body.accessories,
    }
    return {k: v for k, v in raw.items() if v is not None}


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


@router.post("/lock")
async def lock_avatar_face(
    body: AvatarLockRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        overrides = _feature_overrides(body)
        result = fl.lock_dict(
            character_id=body.character_id,
            reference_url=body.reference_url,
            reference_kind=body.reference_kind,
            regenerate_embedding=body.regenerate_embedding,
            feature_overrides=overrides or None,
            identity_strength=body.identity_strength,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Face lock failed") from exc
    return {"ok": True, **result}


@router.post("/verify")
async def verify_avatar_identity(
    body: AvatarVerifyRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        overrides = _feature_overrides(body)
        result = fl.verify_dict(
            character_id=body.character_id,
            feature_overrides=overrides or None,
            candidate_reference_url=body.candidate_reference_url,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Identity verify failed") from exc
    return {"ok": True, **result}


@router.post("/style")
async def set_avatar_style(
    body: AvatarStyleRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        overrides = _style_overrides(body)
        result = ap.style_dict(
            character_id=body.character_id,
            style_preset=body.style_preset,
            overrides=overrides or None,
            hairstyle=body.hairstyle,
            hair_color=body.hair_color,
            beard_style=body.beard_style,
            accessories=body.accessories,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Style apply failed") from exc
    return {"ok": True, **result}


@router.post("/outfit")
async def set_avatar_outfit(
    body: AvatarOutfitRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        result = ap.outfit_dict(
            character_id=body.character_id,
            outfit_id=body.outfit_id,
            category=body.category,
            custom_name=body.custom_name,
            clothing_style=body.clothing_style,
            shoes=body.shoes,
            accessories=body.accessories,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Outfit apply failed") from exc
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


@router.get("/identity/{character_id}")
async def get_avatar_identity(
    character_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    payload = fl.get_identity(character_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Identity lock not found")
    return {"ok": True, **payload}


@router.get("/style/{character_id}")
async def get_avatar_style(
    character_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    payload = ap.get_style(character_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Appearance style not found")
    return {"ok": True, **payload}


@router.get("/outfits/{character_id}")
async def get_avatar_outfits(
    character_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    payload = ap.get_outfits(character_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Outfits not found")
    return {"ok": True, **payload}


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
