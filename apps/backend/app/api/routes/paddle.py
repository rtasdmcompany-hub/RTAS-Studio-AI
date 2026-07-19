"""Paddle webhook & status APIs — Phase 8 Sprint 2."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Request

from app.core.backend_auth import require_backend_secret
from app.core.config import settings
from app.core.runtime import is_production
from app.services import paddle_billing as pb
from app.services.multi_tenant.validation import ValidationError
from app.services.paddle_billing.signatures import SignatureError

router = APIRouter(prefix="/paddle", tags=["paddle-billing"])


def _auth(secret: str | None) -> None:
    require_backend_secret(x_rtas_backend_secret=secret)


def _svc():
    return pb.get_paddle_billing_service()


@router.get("/status")
async def paddle_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().status()


@router.get("/products")
async def paddle_products(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().products.list_products()


@router.post("/webhook")
async def paddle_webhook(
    request: Request,
    paddle_signature: str | None = Header(None, alias="Paddle-Signature"),
):
    """
    Public webhook endpoint — authenticated via Paddle-Signature HMAC.
    Does not require X-Rtas-Backend-Secret.
    """
    import os

    raw = await request.body()
    # Fail closed in production: unsigned only in development with explicit opt-in.
    allow_unsigned = (
        not is_production()
        and os.environ.get("ALLOW_UNSIGNED_WEBHOOKS", "").strip() == "1"
        and not bool((settings.paddle_webhook_secret or "").strip())
    )
    try:
        return _svc().webhooks.process(
            raw_body=raw,
            signature_header=paddle_signature,
            allow_unsigned=allow_unsigned,
        )
    except SignatureError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Webhook processing failed") from exc
