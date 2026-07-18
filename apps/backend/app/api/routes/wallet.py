"""Credit wallet APIs — Phase 8 Sprint 3."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import payment_processing as pp
from app.services.enterprise_auth.errors import AccessError
from app.services.multi_tenant.validation import ValidationError

router = APIRouter(prefix="/wallet", tags=["credit-wallet"])


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
    return HTTPException(status_code=500, detail="Wallet operation failed")


def _user(user_id: str | None) -> str:
    if not user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    return user_id


class PurchaseRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    pack_key: str = Field("pack_500", alias="packKey")
    award_trial: bool = Field(False, alias="awardTrial")
    award_promo: bool = Field(False, alias="awardPromo")
    trial_credits: int | None = Field(None, alias="trialCredits")
    promo_credits: int | None = Field(None, alias="promoCredits")
    model_config = {"populate_by_name": True}


class RefundRequestBody(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    credits: int | None = None
    amount_usd: float | None = Field(None, alias="amountUsd")
    payment_id: str | None = Field(None, alias="paymentId")
    reason: str = "customer_request"
    auto_process: bool = Field(True, alias="autoProcess")
    model_config = {"populate_by_name": True}


@router.get("/status")
async def wallet_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().status()


@router.get("")
async def get_wallet(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().wallets.get(actor_id=actor, organization_id=organization_id)
    except Exception as exc:
        raise _map(exc) from exc


@router.get("/history")
async def wallet_history(
    organization_id: str = Query(..., alias="organizationId"),
    limit: int = Query(100, ge=1, le=500),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().transactions.history(
            actor_id=actor, organization_id=organization_id, limit=limit
        )
    except Exception as exc:
        raise _map(exc) from exc


@router.post("/purchase")
async def wallet_purchase(
    body: PurchaseRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().purchases.purchase(
            body.model_dump(by_alias=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@router.post("/refund")
async def wallet_refund(
    body: RefundRequestBody,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().refunds.request(
            body.model_dump(by_alias=True, exclude_none=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc
