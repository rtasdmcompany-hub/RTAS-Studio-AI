"""PayPal payment APIs — Phase 8 Sprint 3."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import payment_processing as pp
from app.services.enterprise_auth.errors import AccessError
from app.services.multi_tenant.validation import ValidationError
from app.services.payment_processing.signatures import SignatureError

router = APIRouter(prefix="/paypal", tags=["paypal-payments"])


def _auth(secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if expected and (secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _svc():
    return pp.get_payment_processing_service()


def _map(exc: Exception) -> HTTPException:
    if isinstance(exc, AccessError):
        return HTTPException(
            status_code=exc.status_code,
            detail={"error": exc.code, "message": exc.message},
        )
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=500, detail="PayPal operation failed")


def _user(user_id: str | None) -> str:
    if not user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    return user_id


class CreateOrderRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    pack_key: str = Field("pack_500", alias="packKey")
    model_config = {"populate_by_name": True}


class CaptureOrderRequest(BaseModel):
    order_id: str = Field(..., alias="orderId")
    capture_id: str | None = Field(None, alias="captureId")
    payer_email: str | None = Field(None, alias="payerEmail")
    capture: dict[str, Any] | None = None
    model_config = {"populate_by_name": True}


@router.get("/status")
async def paypal_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().status()


@router.post("/create-order")
async def create_order(
    body: CreateOrderRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().paypal.create_order(
            body.model_dump(by_alias=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@router.post("/capture-order")
async def capture_order(
    body: CaptureOrderRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().paypal.capture_order(
            body.model_dump(by_alias=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@router.post("/webhook")
async def paypal_webhook(
    request: Request,
    paypal_transmission_id: str | None = Header(None, alias="Paypal-Transmission-Id"),
    paypal_transmission_time: str | None = Header(None, alias="Paypal-Transmission-Time"),
    paypal_transmission_sig: str | None = Header(None, alias="Paypal-Transmission-Sig"),
):
    raw = await request.body()
    allow_unsigned = not bool(
        (getattr(settings, "paypal_webhook_id", None) or "").strip()
        or __import__("os").environ.get("PAYPAL_WEBHOOK_ID", "").strip()
        or __import__("os").environ.get("PAYPAL_WEBHOOK_SECRET", "").strip()
    )
    try:
        return _svc().paypal.webhook(
            raw_body=raw,
            transmission_id=paypal_transmission_id,
            transmission_time=paypal_transmission_time,
            transmission_sig=paypal_transmission_sig,
            allow_unsigned=allow_unsigned,
        )
    except SignatureError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="PayPal webhook failed") from exc
