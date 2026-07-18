"""Referral, Affiliate & Commission Engine — Phase 8 Sprint 6."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from app.services.referral_affiliate import store
from app.services.referral_affiliate.catalog import (
    AFFILIATE_LINK_BASE,
    AFFILIATE_STATUSES,
    COMMISSION_KINDS,
    COMMISSION_STATUSES,
    COMMISSION_TYPES,
    DEFAULT_COMMISSION_PCT,
    MAX_COMMISSION_LEVELS,
    MIN_PAYOUT_THRESHOLD_USD,
    PAYOUT_METHODS,
    PAYOUT_STATUSES,
    RECURRING_COMMISSION_PCT,
    REFERRAL_LINK_BASE,
    REFERRAL_STATUSES,
    REFERRED_BONUS_CREDITS,
    REFERRER_REWARD_CREDITS,
    generate_code,
    level_rate_pct,
)
from app.services.referral_affiliate.models import (
    Affiliate,
    AffiliateCampaign,
    AffiliateClick,
    AffiliateConversion,
    Commission,
    PayoutHistoryEntry,
    PayoutRequest,
    Referral,
    ReferralCode,
    new_id,
)
from app.services.referral_affiliate.version import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    PHASE,
    SPRINT,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _validation():
    from app.services.multi_tenant.validation import ValidationError, require_non_empty

    return ValidationError, require_non_empty


def _auth_errors():
    from app.services.enterprise_auth.errors import ForbiddenError, NotFoundError

    return ForbiddenError, NotFoundError


def _require_access(**kwargs: Any) -> None:
    from app.services.enterprise_auth.middleware import require_access

    require_access(**kwargs)


def _repo():
    from app.services.multi_tenant.repository import get_repository

    return get_repository()


def _audit(action: str, actor_id: str, detail: str | None = None, **meta: Any) -> None:
    from app.services.enterprise_auth.audit import log_auth_event

    log_auth_event(
        action,
        actor_id=actor_id,
        success=True,
        detail=detail or action,
        metadata=meta,
    )


def _require_read(*, actor_id: str, organization_id: str) -> None:
    _require_access(
        user_id=actor_id,
        organization_id=organization_id,
        permission="org.read",
    )


def _require_manage(*, actor_id: str, organization_id: str) -> None:
    _require_access(
        user_id=actor_id,
        organization_id=organization_id,
        permission="org.update",
    )


def _require_org_exists(organization_id: str) -> None:
    _, NotFoundError = _auth_errors()
    if _repo().get_organization(organization_id) is None:
        raise NotFoundError("organization not found")


def _grant_wallet_credits(
    organization_id: str, credits: int, *, reason: str, actor_id: str
) -> bool:
    """Best-effort credit grant via the payment-processing wallet."""
    try:
        from app.services.payment_processing.service import (
            get_payment_processing_service,
        )

        svc = get_payment_processing_service()
        svc.txns.credit(
            organization_id,
            credits,
            txn_type="bonus",
            credit_category="bonus",
            actor_id=actor_id,
            reason=reason,
            reference_type="referral_reward",
            reference_id=None,
        )
        return True
    except Exception:
        return False


class ReferralRewardEngine:
    """Grants referral rewards once a referral converts."""

    def grant(self, referral: Referral, *, actor_id: str) -> Referral:
        if referral.status == "rewarded":
            return referral
        referral.reward_credits = REFERRER_REWARD_CREDITS
        referral.referred_bonus_credits = REFERRED_BONUS_CREDITS
        referral.status = "rewarded"
        referral.rewarded_at = _now()
        referral.updated_at = _now()
        wallet_synced = _grant_wallet_credits(
            referral.organization_id,
            REFERRER_REWARD_CREDITS,
            reason=f"referral reward for {referral.code}",
            actor_id=actor_id,
        )
        referral.metadata["walletSynced"] = wallet_synced
        store.save_referral(referral)
        _audit(
            "referral.reward.granted",
            actor_id,
            referral.code,
            organizationId=referral.organization_id,
            rewardCredits=REFERRER_REWARD_CREDITS,
            referredBonusCredits=REFERRED_BONUS_CREDITS,
        )
        return referral


class ReferralEngine:
    def __init__(self) -> None:
        self.rewards = ReferralRewardEngine()

    def create_code(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            _, require_non_empty = _validation()
            org_id = require_non_empty(
                payload.get("organizationId") or payload.get("organization_id"),
                "organizationId",
            )
            _require_read(actor_id=actor_id, organization_id=org_id)
            _require_org_exists(org_id)
            code = generate_code("RTAS")
            while store.get_referral_code_by_code(code) is not None:
                code = generate_code("RTAS")
            rc = ReferralCode(
                id=new_id("refc_"),
                organization_id=org_id,
                owner_user_id=actor_id,
                code=code,
                link=f"{REFERRAL_LINK_BASE}{code}",
                max_uses=int(payload.get("maxUses") or 0),
            )
            store.save_referral_code(rc)
            _audit(
                "referral.code.created",
                actor_id,
                code,
                organizationId=org_id,
            )
            return {"ok": True, "referralCode": rc.to_dict()}

    def invite(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = require_non_empty(
                payload.get("organizationId") or payload.get("organization_id"),
                "organizationId",
            )
            _require_read(actor_id=actor_id, organization_id=org_id)
            code = str(require_non_empty(payload.get("code"), "code"))
            rc = store.get_referral_code_by_code(code)
            if rc is None or rc.organization_id != org_id:
                raise ValidationError("referral code not found")
            if not rc.active:
                raise ValidationError("referral code is inactive")
            emails = payload.get("emails") or []
            if not emails:
                raise ValidationError("emails required")
            invited: list[dict[str, Any]] = []
            for email in emails:
                ref = Referral(
                    id=new_id("refl_"),
                    organization_id=org_id,
                    referral_code_id=rc.id,
                    code=rc.code,
                    referrer_user_id=rc.owner_user_id,
                    referred_email=str(email).strip().lower(),
                )
                store.save_referral(ref)
                invited.append(ref.to_dict())
            _audit(
                "referral.invited",
                actor_id,
                rc.code,
                organizationId=org_id,
                count=len(invited),
            )
            return {"ok": True, "count": len(invited), "referrals": invited}

    def track_signup(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        """Referral tracking: a new user signed up with a referral code."""
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            code = str(require_non_empty(payload.get("code"), "code"))
            referred_user = str(
                require_non_empty(
                    payload.get("referredUserId") or payload.get("referred_user_id"),
                    "referredUserId",
                )
            )
            rc = store.get_referral_code_by_code(code)
            if rc is None or not rc.active:
                raise ValidationError("referral code not found or inactive")
            if rc.max_uses and rc.uses >= rc.max_uses:
                raise ValidationError("referral code usage limit reached")
            if store.find_referral_by_referred_user(referred_user) is not None:
                raise ValidationError("user already referred")

            email = str(payload.get("email") or "").strip().lower()
            referral = None
            if email:
                for r in store.list_referrals(rc.organization_id):
                    if r.referred_email == email and r.status == "invited":
                        referral = r
                        break
            if referral is None:
                referral = Referral(
                    id=new_id("refl_"),
                    organization_id=rc.organization_id,
                    referral_code_id=rc.id,
                    code=rc.code,
                    referrer_user_id=rc.owner_user_id,
                    referred_email=email,
                )
            referral.referred_user_id = referred_user
            referral.status = "signed_up"
            referral.signed_up_at = _now()
            referral.updated_at = _now()
            store.save_referral(referral)
            rc.uses += 1
            rc.updated_at = _now()
            store.save_referral_code(rc)
            _audit(
                "referral.signup.tracked",
                actor_id,
                rc.code,
                organizationId=rc.organization_id,
                referredUserId=referred_user,
            )
            return {"ok": True, "referral": referral.to_dict()}

    def mark_converted(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        """Successful referral detection: referred user made a purchase/subscription."""
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            referred_user = str(
                require_non_empty(
                    payload.get("referredUserId") or payload.get("referred_user_id"),
                    "referredUserId",
                )
            )
            referral = store.find_referral_by_referred_user(referred_user)
            if referral is None:
                raise ValidationError("no referral found for user")
            if referral.status in {"converted", "rewarded"}:
                return {"ok": True, "duplicate": True, "referral": referral.to_dict()}
            referral.status = "converted"
            referral.converted_at = _now()
            referral.updated_at = _now()
            store.save_referral(referral)
            referral = self.rewards.grant(referral, actor_id=actor_id)
            _audit(
                "referral.converted",
                actor_id,
                referral.code,
                organizationId=referral.organization_id,
                referredUserId=referred_user,
            )
            return {"ok": True, "referral": referral.to_dict()}

    def list(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        with store.timed_op():
            _require_read(actor_id=actor_id, organization_id=organization_id)
            codes = store.list_referral_codes(organization_id)
            referrals = store.list_referrals(organization_id)
            successful = [r for r in referrals if r.status in {"converted", "rewarded"}]
            return {
                "ok": True,
                "codes": [c.to_dict() for c in codes],
                "totals": {
                    "codes": len(codes),
                    "referrals": len(referrals),
                    "successful": len(successful),
                    "rewardCreditsEarned": sum(r.reward_credits for r in referrals),
                },
                "referrals": [r.to_dict() for r in referrals[:50]],
            }

    def history(
        self, *, actor_id: str, organization_id: str, limit: int = 100
    ) -> dict[str, Any]:
        with store.timed_op():
            _require_read(actor_id=actor_id, organization_id=organization_id)
            items = store.list_referrals(organization_id, limit=limit)
            return {
                "ok": True,
                "count": len(items),
                "history": [r.to_dict() for r in items],
            }


class CommissionEngine:
    def create_for_conversion(
        self,
        affiliate: Affiliate,
        conversion: AffiliateConversion,
        *,
        actor_id: str,
    ) -> list[Commission]:
        """Create level-1 commission plus multi-level overrides for parents."""
        commissions: list[Commission] = []
        current: Affiliate | None = affiliate
        level = 1
        while current is not None and level <= MAX_COMMISSION_LEVELS:
            if level == 1:
                if current.commission_type == "fixed":
                    rate = current.commission_rate
                    amount = current.commission_rate
                elif conversion.kind == "recurring":
                    rate = current.recurring_rate_pct
                    amount = conversion.amount_usd * rate / 100.0
                else:
                    rate = current.commission_rate or DEFAULT_COMMISSION_PCT
                    amount = conversion.amount_usd * rate / 100.0
                ctype = current.commission_type
            else:
                rate = level_rate_pct(level)
                amount = conversion.amount_usd * rate / 100.0
                ctype = "percentage"
            amount = round(amount, 4)
            if amount <= 0:
                break
            com = Commission(
                id=new_id("com_"),
                affiliate_id=current.id,
                organization_id=current.organization_id,
                conversion_id=conversion.id,
                level=level,
                commission_type=ctype,
                kind=conversion.kind,
                base_amount_usd=conversion.amount_usd,
                rate=rate,
                amount_usd=amount,
            )
            store.save_commission(com)
            commissions.append(com)
            current.pending_usd = round(current.pending_usd + amount, 4)
            current.lifetime_usd = round(current.lifetime_usd + amount, 4)
            current.updated_at = _now()
            store.save_affiliate(current)
            _audit(
                "affiliate.commission.created",
                actor_id,
                com.id,
                organizationId=current.organization_id,
                affiliateId=current.id,
                level=level,
                amountUsd=amount,
            )
            current = (
                store.get_affiliate(current.parent_affiliate_id)
                if current.parent_affiliate_id
                else None
            )
            level += 1
        return commissions

    def approve(self, commission_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            _, NotFoundError = _auth_errors()
            com = store.get_commission(commission_id)
            if com is None:
                raise NotFoundError("commission not found")
            _require_manage(actor_id=actor_id, organization_id=com.organization_id)
            if com.status != "pending":
                raise ValidationError(f"cannot approve commission in status {com.status}")
            com.status = "approved"
            com.approved_at = _now()
            com.updated_at = _now()
            store.save_commission(com)
            aff = store.get_affiliate(com.affiliate_id)
            if aff is not None:
                aff.pending_usd = round(max(0.0, aff.pending_usd - com.amount_usd), 4)
                aff.approved_usd = round(aff.approved_usd + com.amount_usd, 4)
                aff.updated_at = _now()
                store.save_affiliate(aff)
            _audit(
                "affiliate.commission.approved",
                actor_id,
                com.id,
                organizationId=com.organization_id,
                amountUsd=com.amount_usd,
            )
            return {"ok": True, "commission": com.to_dict()}

    def list(
        self,
        *,
        actor_id: str,
        organization_id: str,
        affiliate_id: str | None = None,
        status: str | None = None,
        limit: int = 200,
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            _require_read(actor_id=actor_id, organization_id=organization_id)
            if status is not None and status not in COMMISSION_STATUSES:
                raise ValidationError(f"unknown commission status: {status}")
            items = store.list_commissions(
                organization_id=organization_id,
                affiliate_id=affiliate_id,
                status=status,
                limit=limit,
            )
            return {
                "ok": True,
                "count": len(items),
                "totals": {
                    "pendingUsd": round(
                        sum(c.amount_usd for c in items if c.status == "pending"), 4
                    ),
                    "approvedUsd": round(
                        sum(c.amount_usd for c in items if c.status == "approved"), 4
                    ),
                    "paidUsd": round(
                        sum(c.amount_usd for c in items if c.status == "paid"), 4
                    ),
                },
                "commissions": [c.to_dict() for c in items],
            }


class AffiliateEngine:
    def __init__(self) -> None:
        self.commissions = CommissionEngine()

    def register(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = require_non_empty(
                payload.get("organizationId") or payload.get("organization_id"),
                "organizationId",
            )
            _require_read(actor_id=actor_id, organization_id=org_id)
            _require_org_exists(org_id)
            if store.get_affiliate_by_user(org_id, actor_id) is not None:
                raise ValidationError("user is already an affiliate for this organization")
            ctype = str(payload.get("commissionType") or "percentage")
            if ctype not in COMMISSION_TYPES:
                raise ValidationError(f"unknown commission type: {ctype}")
            method = str(payload.get("payoutMethod") or "paypal")
            if method not in PAYOUT_METHODS:
                raise ValidationError(f"unknown payout method: {method}")
            parent_id = payload.get("parentAffiliateId") or None
            if parent_id and store.get_affiliate(str(parent_id)) is None:
                raise ValidationError("parent affiliate not found")
            aff = Affiliate(
                id=new_id("aff_"),
                organization_id=org_id,
                user_id=actor_id,
                name=str(payload.get("name") or ""),
                email=str(payload.get("email") or ""),
                status="active",
                commission_type=ctype,
                commission_rate=float(
                    payload.get("commissionRate") or DEFAULT_COMMISSION_PCT
                ),
                recurring_rate_pct=float(
                    payload.get("recurringRatePct") or RECURRING_COMMISSION_PCT
                ),
                payout_method=method,
                parent_affiliate_id=str(parent_id) if parent_id else None,
            )
            store.save_affiliate(aff)
            # Default campaign with a tracking link
            campaign = AffiliateCampaign(
                id=new_id("camp_"),
                affiliate_id=aff.id,
                organization_id=org_id,
                name="Default",
                slug=generate_code("AF", 6).lower(),
                link="",
            )
            campaign.link = f"{AFFILIATE_LINK_BASE}{campaign.slug}"
            store.save_campaign(campaign)
            _audit(
                "affiliate.registered",
                actor_id,
                aff.id,
                organizationId=org_id,
            )
            return {
                "ok": True,
                "affiliate": aff.to_dict(),
                "campaign": campaign.to_dict(),
            }

    def _own(self, *, actor_id: str, organization_id: str) -> Affiliate:
        ForbiddenError, _ = _auth_errors()
        _require_read(actor_id=actor_id, organization_id=organization_id)
        aff = store.get_affiliate_by_user(organization_id, actor_id)
        if aff is None:
            raise ForbiddenError("not an affiliate for this organization")
        return aff

    def set_status(
        self, affiliate_id: str, status: str, *, actor_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            _, NotFoundError = _auth_errors()
            if status not in AFFILIATE_STATUSES:
                raise ValidationError(f"unknown affiliate status: {status}")
            aff = store.get_affiliate(affiliate_id)
            if aff is None:
                raise NotFoundError("affiliate not found")
            _require_manage(actor_id=actor_id, organization_id=aff.organization_id)
            aff.status = status
            aff.updated_at = _now()
            store.save_affiliate(aff)
            _audit(
                "affiliate.status.changed",
                actor_id,
                f"{aff.id}:{status}",
                organizationId=aff.organization_id,
            )
            return {"ok": True, "affiliate": aff.to_dict()}

    def create_campaign(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            _, require_non_empty = _validation()
            org_id = require_non_empty(
                payload.get("organizationId") or payload.get("organization_id"),
                "organizationId",
            )
            aff = self._own(actor_id=actor_id, organization_id=org_id)
            name = str(require_non_empty(payload.get("name"), "name"))
            campaign = AffiliateCampaign(
                id=new_id("camp_"),
                affiliate_id=aff.id,
                organization_id=org_id,
                name=name,
                slug=generate_code("AF", 6).lower(),
                link="",
            )
            campaign.link = f"{AFFILIATE_LINK_BASE}{campaign.slug}"
            store.save_campaign(campaign)
            _audit(
                "affiliate.campaign.created",
                actor_id,
                name,
                organizationId=org_id,
                affiliateId=aff.id,
            )
            return {"ok": True, "campaign": campaign.to_dict()}

    def track_click(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            affiliate_id = str(
                require_non_empty(
                    payload.get("affiliateId") or payload.get("affiliate_id"),
                    "affiliateId",
                )
            )
            aff = store.get_affiliate(affiliate_id)
            if aff is None:
                raise ValidationError("affiliate not found")
            if aff.status != "active":
                raise ValidationError("affiliate is not active")
            campaign_id = payload.get("campaignId") or None
            ip = str(payload.get("ip") or "")
            click = AffiliateClick(
                id=new_id("clk_"),
                affiliate_id=aff.id,
                organization_id=aff.organization_id,
                campaign_id=str(campaign_id) if campaign_id else None,
                source=str(payload.get("source") or ""),
                referrer_url=str(payload.get("referrerUrl") or ""),
                ip_hash=hashlib.sha256(ip.encode()).hexdigest()[:16] if ip else "",
                user_agent=str(payload.get("userAgent") or ""),
            )
            store.save_click(click)
            if campaign_id:
                camp = store.get_campaign(str(campaign_id))
                if camp is not None:
                    camp.clicks += 1
                    camp.updated_at = _now()
                    store.save_campaign(camp)
            return {"ok": True, "click": click.to_dict()}

    def track_conversion(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            affiliate_id = str(
                require_non_empty(
                    payload.get("affiliateId") or payload.get("affiliate_id"),
                    "affiliateId",
                )
            )
            aff = store.get_affiliate(affiliate_id)
            if aff is None:
                raise ValidationError("affiliate not found")
            if aff.status != "active":
                raise ValidationError("affiliate is not active")
            amount = float(payload.get("amountUsd") or payload.get("amount") or 0)
            if amount <= 0:
                raise ValidationError("amountUsd must be > 0")
            kind = str(payload.get("kind") or "one_time")
            if kind not in COMMISSION_KINDS:
                raise ValidationError(f"unknown conversion kind: {kind}")
            campaign_id = payload.get("campaignId") or None
            conv = AffiliateConversion(
                id=new_id("conv_"),
                affiliate_id=aff.id,
                organization_id=aff.organization_id,
                campaign_id=str(campaign_id) if campaign_id else None,
                order_ref=str(payload.get("orderRef") or ""),
                kind=kind,
                amount_usd=amount,
            )
            commissions = self.commissions.create_for_conversion(
                aff, conv, actor_id=actor_id
            )
            conv.commission_ids = [c.id for c in commissions]
            store.save_conversion(conv)
            if campaign_id:
                camp = store.get_campaign(str(campaign_id))
                if camp is not None:
                    camp.conversions += 1
                    camp.revenue_usd = round(camp.revenue_usd + amount, 4)
                    camp.updated_at = _now()
                    store.save_campaign(camp)
            _audit(
                "affiliate.conversion.tracked",
                actor_id,
                conv.id,
                organizationId=aff.organization_id,
                affiliateId=aff.id,
                amountUsd=amount,
            )
            return {
                "ok": True,
                "conversion": conv.to_dict(),
                "commissions": [c.to_dict() for c in commissions],
            }

    def dashboard(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        with store.timed_op():
            aff = self._own(actor_id=actor_id, organization_id=organization_id)
            campaigns = store.list_campaigns(aff.id)
            conversions = store.list_conversions(aff.id)
            clicks = store.count_clicks(aff.id)
            commissions = store.list_commissions(affiliate_id=aff.id)
            return {
                "ok": True,
                "affiliate": aff.to_dict(),
                "campaigns": [c.to_dict() for c in campaigns],
                "stats": {
                    "clicks": clicks,
                    "conversions": len(conversions),
                    "conversionRatePct": round(
                        (len(conversions) / clicks * 100.0) if clicks else 0.0, 2
                    ),
                    "salesUsd": round(sum(c.amount_usd for c in conversions), 4),
                    "commissionCount": len(commissions),
                    "pendingUsd": aff.pending_usd,
                    "approvedUsd": aff.approved_usd,
                    "paidUsd": aff.paid_usd,
                    "lifetimeUsd": aff.lifetime_usd,
                },
                "recentConversions": [c.to_dict() for c in conversions[:10]],
            }


class PayoutEngine:
    def request(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            ForbiddenError, _ = _auth_errors()
            org_id = require_non_empty(
                payload.get("organizationId") or payload.get("organization_id"),
                "organizationId",
            )
            _require_read(actor_id=actor_id, organization_id=org_id)
            aff = store.get_affiliate_by_user(org_id, actor_id)
            if aff is None:
                raise ForbiddenError("not an affiliate for this organization")
            amount = float(payload.get("amountUsd") or payload.get("amount") or aff.approved_usd)
            if amount < MIN_PAYOUT_THRESHOLD_USD:
                raise ValidationError(
                    f"minimum payout threshold is ${MIN_PAYOUT_THRESHOLD_USD:.2f}"
                )
            if amount > aff.approved_usd:
                raise ValidationError("payout amount exceeds approved commission balance")
            approved = store.list_commissions(affiliate_id=aff.id, status="approved")
            payout = PayoutRequest(
                id=new_id("pout_"),
                affiliate_id=aff.id,
                organization_id=org_id,
                amount_usd=round(amount, 4),
                method=str(payload.get("method") or aff.payout_method),
                note=str(payload.get("note") or ""),
                commission_ids=[c.id for c in approved],
            )
            store.save_payout(payout)
            self._history(payout, "requested", actor_id=actor_id)
            _audit(
                "affiliate.payout.requested",
                actor_id,
                payout.id,
                organizationId=org_id,
                amountUsd=payout.amount_usd,
            )
            return {"ok": True, "payout": payout.to_dict()}

    def _history(
        self, payout: PayoutRequest, action: str, *, actor_id: str, detail: str = ""
    ) -> None:
        store.save_payout_history(
            PayoutHistoryEntry(
                id=new_id("pouh_"),
                payout_id=payout.id,
                affiliate_id=payout.affiliate_id,
                organization_id=payout.organization_id,
                action=action,
                amount_usd=payout.amount_usd,
                detail=detail,
                actor_id=actor_id,
            )
        )

    def process(
        self, payout_id: str, decision: str, *, actor_id: str, note: str = ""
    ) -> dict[str, Any]:
        """Approve, reject, or mark a payout as paid."""
        with store.timed_op():
            ValidationError, _ = _validation()
            _, NotFoundError = _auth_errors()
            if decision not in {"approved", "rejected", "paid"}:
                raise ValidationError(f"unknown payout decision: {decision}")
            payout = store.get_payout(payout_id)
            if payout is None:
                raise NotFoundError("payout request not found")
            _require_manage(actor_id=actor_id, organization_id=payout.organization_id)
            allowed = {
                "approved": {"requested"},
                "rejected": {"requested", "approved"},
                "paid": {"approved"},
            }
            if payout.status not in allowed[decision]:
                raise ValidationError(
                    f"cannot mark payout {decision} from status {payout.status}"
                )
            payout.status = decision
            payout.processed_at = _now()
            payout.note = note or payout.note
            payout.updated_at = _now()
            store.save_payout(payout)
            self._history(payout, decision, actor_id=actor_id, detail=note)

            aff = store.get_affiliate(payout.affiliate_id)
            if decision == "paid" and aff is not None:
                remaining = payout.amount_usd
                for cid in payout.commission_ids:
                    if remaining <= 0:
                        break
                    com = store.get_commission(cid)
                    if com is None or com.status != "approved":
                        continue
                    com.status = "paid"
                    com.paid_at = _now()
                    com.payout_id = payout.id
                    com.updated_at = _now()
                    store.save_commission(com)
                    remaining = round(remaining - com.amount_usd, 4)
                aff.approved_usd = round(max(0.0, aff.approved_usd - payout.amount_usd), 4)
                aff.paid_usd = round(aff.paid_usd + payout.amount_usd, 4)
                aff.updated_at = _now()
                store.save_affiliate(aff)
            _audit(
                f"affiliate.payout.{decision}",
                actor_id,
                payout.id,
                organizationId=payout.organization_id,
                amountUsd=payout.amount_usd,
            )
            return {"ok": True, "payout": payout.to_dict()}

    def history(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        with store.timed_op():
            ForbiddenError, _ = _auth_errors()
            _require_read(actor_id=actor_id, organization_id=organization_id)
            aff = store.get_affiliate_by_user(organization_id, actor_id)
            if aff is None:
                raise ForbiddenError("not an affiliate for this organization")
            entries = store.list_payout_history(aff.id)
            payouts = store.list_payouts(affiliate_id=aff.id)
            return {
                "ok": True,
                "payouts": [p.to_dict() for p in payouts],
                "history": [h.to_dict() for h in entries],
            }

    def statement(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        """Commission statement for the requesting affiliate."""
        with store.timed_op():
            ForbiddenError, _ = _auth_errors()
            _require_read(actor_id=actor_id, organization_id=organization_id)
            aff = store.get_affiliate_by_user(organization_id, actor_id)
            if aff is None:
                raise ForbiddenError("not an affiliate for this organization")
            commissions = store.list_commissions(affiliate_id=aff.id)
            return {
                "ok": True,
                "affiliateId": aff.id,
                "statement": {
                    "pendingUsd": aff.pending_usd,
                    "approvedUsd": aff.approved_usd,
                    "paidUsd": aff.paid_usd,
                    "lifetimeUsd": aff.lifetime_usd,
                    "minPayoutThresholdUsd": MIN_PAYOUT_THRESHOLD_USD,
                    "eligibleForPayout": aff.approved_usd >= MIN_PAYOUT_THRESHOLD_USD,
                },
                "commissions": [c.to_dict() for c in commissions],
            }


class AffiliateAnalyticsEngine:
    def analytics(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        with store.timed_op():
            _require_read(actor_id=actor_id, organization_id=organization_id)
            referrals = store.list_referrals(organization_id, limit=10_000)
            successful = [r for r in referrals if r.status in {"converted", "rewarded"}]
            affiliates = store.list_affiliates(organization_id)
            commissions = store.list_commissions(organization_id=organization_id, limit=10_000)
            total_clicks = sum(store.count_clicks(a.id) for a in affiliates)
            conversions: list[AffiliateConversion] = []
            for a in affiliates:
                conversions.extend(store.list_conversions(a.id, limit=10_000))
            sales_usd = round(sum(c.amount_usd for c in conversions), 4)
            return {
                "ok": True,
                "organizationId": organization_id,
                "analytics": {
                    "totalReferrals": len(referrals),
                    "successfulReferrals": len(successful),
                    "referralRewardCredits": sum(r.reward_credits for r in referrals),
                    "affiliates": len(affiliates),
                    "clicks": total_clicks,
                    "conversions": len(conversions),
                    "conversionRatePct": round(
                        (len(conversions) / total_clicks * 100.0) if total_clicks else 0.0,
                        2,
                    ),
                    "affiliateSalesUsd": sales_usd,
                    "commissionEarnedUsd": round(
                        sum(c.amount_usd for c in commissions), 4
                    ),
                    "commissionPaidUsd": round(
                        sum(c.amount_usd for c in commissions if c.status == "paid"), 4
                    ),
                    "pendingCommissionUsd": round(
                        sum(c.amount_usd for c in commissions if c.status == "pending"), 4
                    ),
                    "approvedCommissionUsd": round(
                        sum(c.amount_usd for c in commissions if c.status == "approved"),
                        4,
                    ),
                },
            }


class ReferralAffiliateService:
    def __init__(self) -> None:
        self.referrals = ReferralEngine()
        self.rewards = self.referrals.rewards
        self.affiliates = AffiliateEngine()
        self.commissions = self.affiliates.commissions
        self.payouts = PayoutEngine()
        self.analytics = AffiliateAnalyticsEngine()

    def status(self) -> dict[str, Any]:
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "label": ENGINE_LABEL,
            "phase": PHASE,
            "sprint": SPRINT,
            "engines": {
                "referrals": "ready",
                "affiliates": "ready",
                "commissions": "ready",
                "rewards": "ready",
                "payouts": "ready",
                "analytics": "ready",
            },
            "referralStatuses": list(REFERRAL_STATUSES),
            "affiliateStatuses": list(AFFILIATE_STATUSES),
            "commissionStatuses": list(COMMISSION_STATUSES),
            "payoutStatuses": list(PAYOUT_STATUSES),
            "minPayoutThresholdUsd": MIN_PAYOUT_THRESHOLD_USD,
            "maxCommissionLevels": MAX_COMMISSION_LEVELS,
            "stats": store.metrics(),
        }


_service: ReferralAffiliateService | None = None


def get_referral_affiliate_service() -> ReferralAffiliateService:
    global _service
    if _service is None:
        _service = ReferralAffiliateService()
    return _service


def reset_engine() -> None:
    global _service
    store.reset_store()
    _service = None


get_engine = get_referral_affiliate_service
