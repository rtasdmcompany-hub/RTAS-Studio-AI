"""Referral & affiliate APIs — Phase 8 Sprint 6."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.backend_auth import require_backend_secret
from app.core.config import settings
from app.services import referral_affiliate as ra_svc
from app.services.enterprise_auth.errors import AccessError
from app.services.multi_tenant.validation import ValidationError

referrals_router = APIRouter(prefix="/referrals", tags=["referrals"])
affiliate_router = APIRouter(prefix="/affiliate", tags=["affiliate"])


def _auth(secret: str | None) -> None:
    require_backend_secret(x_rtas_backend_secret=secret)


def _svc():
    return ra_svc.get_referral_affiliate_service()


def _map(exc: Exception) -> HTTPException:
    if isinstance(exc, AccessError):
        return HTTPException(
            status_code=exc.status_code,
            detail={"error": exc.code, "message": exc.message},
        )
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=500, detail="Referral/affiliate operation failed")


def _user(user_id: str | None) -> str:
    if not user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    return user_id


class ReferralCreateRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    max_uses: int | None = Field(None, alias="maxUses")
    model_config = {"populate_by_name": True}


class ReferralInviteRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    code: str
    emails: list[str]
    model_config = {"populate_by_name": True}


class ReferralSignupRequest(BaseModel):
    code: str
    referred_user_id: str = Field(..., alias="referredUserId")
    email: str | None = None
    model_config = {"populate_by_name": True}


class ReferralConvertRequest(BaseModel):
    referred_user_id: str = Field(..., alias="referredUserId")
    model_config = {"populate_by_name": True}


class AffiliateRegisterRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    name: str | None = None
    email: str | None = None
    commission_type: str = Field("percentage", alias="commissionType")
    commission_rate: float | None = Field(None, alias="commissionRate")
    payout_method: str = Field("paypal", alias="payoutMethod")
    parent_affiliate_id: str | None = Field(None, alias="parentAffiliateId")
    model_config = {"populate_by_name": True}


class ConversionRequest(BaseModel):
    affiliate_id: str = Field(..., alias="affiliateId")
    amount_usd: float = Field(..., alias="amountUsd")
    kind: str = "one_time"
    campaign_id: str | None = Field(None, alias="campaignId")
    order_ref: str | None = Field(None, alias="orderRef")
    model_config = {"populate_by_name": True}


class ClickRequest(BaseModel):
    affiliate_id: str = Field(..., alias="affiliateId")
    campaign_id: str | None = Field(None, alias="campaignId")
    source: str | None = None
    referrer_url: str | None = Field(None, alias="referrerUrl")
    ip: str | None = None
    user_agent: str | None = Field(None, alias="userAgent")
    model_config = {"populate_by_name": True}


class PayoutRequestBody(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    amount_usd: float | None = Field(None, alias="amountUsd")
    method: str | None = None
    note: str | None = None
    model_config = {"populate_by_name": True}


class PayoutProcessRequest(BaseModel):
    payout_id: str = Field(..., alias="payoutId")
    decision: str
    note: str | None = None
    model_config = {"populate_by_name": True}


# --- Referrals ---


@referrals_router.post("/create")
async def create_referral_code(
    body: ReferralCreateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().referrals.create_code(
            body.model_dump(by_alias=True, exclude_none=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@referrals_router.get("")
async def list_referrals(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().referrals.list(actor_id=actor, organization_id=organization_id)
    except Exception as exc:
        raise _map(exc) from exc


@referrals_router.get("/history")
async def referral_history(
    organization_id: str = Query(..., alias="organizationId"),
    limit: int = Query(100, ge=1, le=500),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().referrals.history(
            actor_id=actor, organization_id=organization_id, limit=limit
        )
    except Exception as exc:
        raise _map(exc) from exc


@referrals_router.post("/invite")
async def invite_referrals(
    body: ReferralInviteRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().referrals.invite(
            body.model_dump(by_alias=True, exclude_none=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@referrals_router.post("/track-signup")
async def track_referral_signup(
    body: ReferralSignupRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().referrals.track_signup(
            body.model_dump(by_alias=True, exclude_none=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@referrals_router.post("/convert")
async def convert_referral(
    body: ReferralConvertRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().referrals.mark_converted(
            body.model_dump(by_alias=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


# --- Affiliate ---


@affiliate_router.post("/register")
async def register_affiliate(
    body: AffiliateRegisterRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().affiliates.register(
            body.model_dump(by_alias=True, exclude_none=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@affiliate_router.get("/dashboard")
async def affiliate_dashboard(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().affiliates.dashboard(
            actor_id=actor, organization_id=organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@affiliate_router.get("/commissions")
async def affiliate_commissions(
    organization_id: str = Query(..., alias="organizationId"),
    status: str | None = Query(None),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().payouts.statement(
            actor_id=actor, organization_id=organization_id
        ) if status is None else _svc().commissions.list(
            actor_id=actor, organization_id=organization_id, status=status
        )
    except Exception as exc:
        raise _map(exc) from exc


@affiliate_router.post("/payout-request")
async def request_payout(
    body: PayoutRequestBody,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().payouts.request(
            body.model_dump(by_alias=True, exclude_none=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@affiliate_router.post("/payout-process")
async def process_payout(
    body: PayoutProcessRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().payouts.process(
            body.payout_id, body.decision, actor_id=actor, note=body.note or ""
        )
    except Exception as exc:
        raise _map(exc) from exc


@affiliate_router.get("/payouts")
async def payout_history(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().payouts.history(actor_id=actor, organization_id=organization_id)
    except Exception as exc:
        raise _map(exc) from exc


@affiliate_router.post("/track-click")
async def track_click(
    body: ClickRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().affiliates.track_click(
            body.model_dump(by_alias=True, exclude_none=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@affiliate_router.post("/track-conversion")
async def track_conversion(
    body: ConversionRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().affiliates.track_conversion(
            body.model_dump(by_alias=True, exclude_none=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@affiliate_router.get("/analytics")
async def affiliate_analytics(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().analytics.analytics(
            actor_id=actor, organization_id=organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@affiliate_router.get("/status")
async def engine_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().status()
