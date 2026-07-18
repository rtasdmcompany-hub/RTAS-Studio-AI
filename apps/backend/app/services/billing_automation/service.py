"""Invoicing, Tax, Coupons & Billing Automation Engine — Phase 8 Sprint 5."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.services.billing_automation import store
from app.services.billing_automation.catalog import (
    DEFAULT_COUPONS,
    MAX_PAYMENT_RETRIES,
    REMINDER_DAYS_BEFORE_RENEWAL,
    RETRY_SCHEDULE_HOURS,
    normalize_country,
    tax_rule_for,
)
from app.services.billing_automation.models import (
    AutomationBillingEvent,
    Coupon,
    CouponUsage,
    DiscountRecord,
    InvoiceItem,
    InvoiceRecord,
    PaymentRetry,
    TaxRecord,
    new_id,
)
from app.services.billing_automation.version import (
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


def _emit(
    organization_id: str,
    event_type: str,
    detail: str = "",
    *,
    actor_id: str | None = None,
    **meta: Any,
) -> AutomationBillingEvent:
    event = AutomationBillingEvent(
        id=new_id("baevt_"),
        organization_id=organization_id,
        event_type=event_type,
        detail=detail,
        actor_id=actor_id,
        metadata=meta,
    )
    store.save_event(event)
    return event


def _plan_price(plan_key: str, billing_cycle: str = "monthly") -> float:
    try:
        from app.services.billing.catalog import DEFAULT_PLANS

        for plan in DEFAULT_PLANS:
            if plan["key"] == plan_key:
                if billing_cycle == "yearly":
                    return float(plan["yearlyPriceUsd"])
                return float(plan["monthlyPriceUsd"])
    except Exception:
        pass
    defaults = {
        "free_trial": 0.0,
        "starter": 29.0,
        "professional": 99.0,
        "business": 299.0,
        "enterprise": 999.0,
    }
    return float(defaults.get(plan_key, 29.0))


class TaxEngine:
    def calculate(
        self,
        *,
        organization_id: str,
        taxable_usd: float,
        country: str | None = None,
        invoice_id: str | None = None,
        persist: bool = True,
    ) -> dict[str, Any]:
        country_code = normalize_country(country)
        rule = tax_rule_for(country_code)
        exempt_reason = store.get_exemption(organization_id)
        exempt = bool(exempt_reason)
        rate = 0.0 if exempt else float(rule["rate"])
        tax_usd = 0.0 if exempt else round(max(0.0, taxable_usd) * rate, 2)
        record = TaxRecord(
            id=new_id("tax_"),
            organization_id=organization_id,
            invoice_id=invoice_id,
            country=country_code,
            tax_type="none" if exempt else str(rule["taxType"]),
            rate=rate,
            taxable_usd=taxable_usd,
            tax_usd=tax_usd,
            exempt=exempt,
            exemption_reason=exempt_reason or "",
        )
        if persist:
            store.save_tax(record)
        return {
            "ok": True,
            "tax": record.to_dict(),
            "rule": rule,
            "country": country_code,
        }

    def get(
        self,
        *,
        actor_id: str,
        organization_id: str,
        country: str | None = None,
        amount_usd: float | None = None,
    ) -> dict[str, Any]:
        _require_read(actor_id=actor_id, organization_id=organization_id)
        country_code = normalize_country(country)
        rule = tax_rule_for(country_code)
        exempt = store.get_exemption(organization_id)
        history = store.list_tax(organization_id, limit=50)
        preview = None
        if amount_usd is not None:
            preview = self.calculate(
                organization_id=organization_id,
                taxable_usd=float(amount_usd),
                country=country_code,
                persist=False,
            )
        return {
            "ok": True,
            "organizationId": organization_id,
            "country": country_code,
            "rule": rule,
            "exempt": bool(exempt),
            "exemptionReason": exempt or "",
            "preview": preview["tax"] if preview else None,
            "history": [t.to_dict() for t in history],
        }

    def set_exemption(
        self, organization_id: str, reason: str, *, actor_id: str
    ) -> dict[str, Any]:
        _require_manage(actor_id=actor_id, organization_id=organization_id)
        store.set_exemption(organization_id, reason)
        _emit(organization_id, "tax.exemption_set", reason, actor_id=actor_id)
        return {"ok": True, "exempt": True, "reason": reason}


class DiscountEngine:
    def compute_amount(self, *, subtotal_usd: float, coupon: Coupon) -> float:
        amount = 0.0
        if coupon.coupon_type in {"percentage", "promotional", "referral"} or (
            coupon.percent_off > 0
        ):
            pct = coupon.percent_off or 0.0
            amount = round(subtotal_usd * (pct / 100.0), 2)
        if coupon.coupon_type == "fixed" or coupon.amount_off_usd > 0:
            amount = max(amount, float(coupon.amount_off_usd))
        return min(amount, max(0.0, subtotal_usd))

    def apply_coupon_discount(
        self,
        *,
        organization_id: str,
        subtotal_usd: float,
        coupon: Coupon,
        invoice_id: str | None = None,
        persist: bool = True,
    ) -> DiscountRecord:
        amount = self.compute_amount(subtotal_usd=subtotal_usd, coupon=coupon)
        discount = DiscountRecord(
            id=new_id("disc_"),
            organization_id=organization_id,
            discount_type=coupon.coupon_type,
            amount_usd=amount,
            percent_off=coupon.percent_off,
            coupon_code=coupon.code,
            invoice_id=invoice_id,
            reason=f"coupon:{coupon.code}",
        )
        if persist:
            store.save_discount(discount)
        return discount


class CouponEngine:
    def __init__(self) -> None:
        self.discounts = DiscountEngine()

    def ensure_defaults(self) -> None:
        if store.list_coupons():
            return
        now = _now()
        for raw in DEFAULT_COUPONS:
            coupon = Coupon(
                id=new_id("cpn_"),
                code=str(raw["code"]).upper(),
                coupon_type=str(raw["couponType"]),
                percent_off=float(raw.get("percentOff") or 0),
                amount_off_usd=float(raw.get("amountOffUsd") or 0),
                category=str(raw.get("category") or "promotional"),
                max_redemptions=int(raw.get("maxRedemptions") or 100),
                per_org_limit=int(raw.get("perOrgLimit") or 1),
                trial_days=int(raw.get("trialDays") or 0),
                expires_at=now + timedelta(days=365),
            )
            store.save_coupon(coupon)

    def validate(
        self, payload: dict[str, Any], *, actor_id: str
    ) -> dict[str, Any]:
        ValidationError, require_non_empty = _validation()
        self.ensure_defaults()
        org_id = require_non_empty(
            payload.get("organizationId") or payload.get("organization_id"),
            "organizationId",
        )
        code = require_non_empty(payload.get("code") or payload.get("couponCode"), "code")
        _require_read(actor_id=actor_id, organization_id=org_id)
        coupon = store.get_coupon_by_code(str(code))
        if coupon is None or not coupon.active:
            raise ValidationError("invalid coupon code")
        if coupon.expires_at and coupon.expires_at < _now():
            raise ValidationError("coupon expired")
        if coupon.redemption_count >= coupon.max_redemptions:
            raise ValidationError("coupon usage limit reached")
        org_uses = store.list_coupon_usage(org_id, coupon_code=coupon.code)
        if len(org_uses) >= coupon.per_org_limit:
            raise ValidationError("coupon already used by organization")
        subtotal = float(payload.get("subtotalUsd") or payload.get("amount") or 0)
        preview_base = subtotal if subtotal > 0 else 100.0
        estimated = self.discounts.compute_amount(
            subtotal_usd=preview_base, coupon=coupon
        )
        return {
            "ok": True,
            "valid": True,
            "coupon": coupon.to_dict(),
            "estimatedDiscountUsd": estimated,
            "trialDays": coupon.trial_days,
        }

    def apply(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        ValidationError, require_non_empty = _validation()
        self.ensure_defaults()
        org_id = require_non_empty(
            payload.get("organizationId") or payload.get("organization_id"),
            "organizationId",
        )
        code = require_non_empty(payload.get("code") or payload.get("couponCode"), "code")
        _require_manage(actor_id=actor_id, organization_id=org_id)
        # Re-validate
        validated = self.validate(payload, actor_id=actor_id)
        coupon = store.get_coupon_by_code(str(code))
        assert coupon is not None
        subtotal = float(payload.get("subtotalUsd") or payload.get("amount") or 0)
        discount = self.discounts.apply_coupon_discount(
            organization_id=org_id,
            subtotal_usd=subtotal if subtotal > 0 else 0.0,
            coupon=coupon,
            invoice_id=payload.get("invoiceId"),
        )
        coupon.redemption_count += 1
        store.save_coupon(coupon)
        usage = CouponUsage(
            id=new_id("cpu_"),
            coupon_id=coupon.id,
            coupon_code=coupon.code,
            organization_id=org_id,
            actor_id=actor_id,
            discount_usd=discount.amount_usd,
            invoice_id=payload.get("invoiceId"),
        )
        store.save_coupon_usage(usage)
        _emit(
            org_id,
            "coupon.applied",
            coupon.code,
            actor_id=actor_id,
            discountUsd=discount.amount_usd,
        )
        _audit("billing.coupon.applied", actor_id, coupon.code, organizationId=org_id)
        return {
            "ok": True,
            "coupon": coupon.to_dict(),
            "discount": discount.to_dict(),
            "usage": usage.to_dict(),
            "trialDays": coupon.trial_days,
            "validated": validated["valid"],
        }


class InvoiceEngine:
    def __init__(self) -> None:
        self.tax = TaxEngine()
        self.coupons = CouponEngine()

    def _next_number(self) -> str:
        seq = store.next_invoice_seq()
        return f"INV-{_now().strftime('%Y%m%d')}-{seq:05d}"

    def generate(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            _, NotFoundError = _auth_errors()
            org_id = require_non_empty(
                payload.get("organizationId") or payload.get("organization_id"),
                "organizationId",
            )
            _require_manage(actor_id=actor_id, organization_id=org_id)
            if _repo().get_organization(org_id) is None:
                raise NotFoundError("organization not found")

            plan_key = str(payload.get("planKey") or payload.get("plan") or "starter")
            cycle = str(payload.get("billingCycle") or "monthly")
            country = normalize_country(payload.get("country"))
            subtotal = float(
                payload.get("subtotalUsd")
                if payload.get("subtotalUsd") is not None
                else _plan_price(plan_key, cycle)
            )
            if subtotal < 0:
                raise ValidationError("subtotal must be >= 0")

            discount_usd = 0.0
            coupon_code = payload.get("couponCode") or payload.get("code")
            if coupon_code:
                applied = self.coupons.apply(
                    {
                        "organizationId": org_id,
                        "code": coupon_code,
                        "subtotalUsd": subtotal,
                    },
                    actor_id=actor_id,
                )
                discount_usd = float(applied["discount"]["amountUsd"])
                coupon_code = applied["coupon"]["code"]

            taxable = max(0.0, subtotal - discount_usd)
            tax_result = self.tax.calculate(
                organization_id=org_id,
                taxable_usd=taxable,
                country=country,
                persist=False,
            )
            tax_usd = float(tax_result["tax"]["taxUsd"])
            total = round(taxable + tax_usd, 2)
            now = _now()
            status = str(payload.get("status") or ("paid" if total == 0 else "pending"))
            invoice_number = self._next_number()
            receipt_number = None
            if status == "paid":
                receipt_number = f"RCT-{now.strftime('%Y%m%d')}-{store.next_invoice_seq():05d}"
            inv = InvoiceRecord(
                id=new_id("binv_"),
                organization_id=org_id,
                invoice_number=invoice_number,
                status=status,
                subtotal_usd=subtotal,
                discount_usd=discount_usd,
                tax_usd=tax_usd,
                total_usd=total,
                tax_type=tax_result["tax"]["taxType"],
                tax_rate=float(tax_result["tax"]["rate"]),
                country=country,
                plan_key=plan_key,
                billing_cycle=cycle,
                coupon_code=coupon_code,
                actor_id=actor_id,
                period_start=now,
                period_end=now + timedelta(days=365 if cycle == "yearly" else 30),
                issued_at=now,
                due_at=now + timedelta(days=14),
                paid_at=now if status == "paid" else None,
                pdf_metadata={
                    "title": f"Invoice {invoice_number}",
                    "template": "rtas_enterprise_v1",
                    "currency": "USD",
                    "seller": "RTAS Studio AI",
                    "buyerOrganizationId": org_id,
                    "lineItemCount": 1,
                    "generatedAt": now.isoformat().replace("+00:00", "Z"),
                },
                receipt_number=receipt_number,
            )
            store.save_invoice(inv)

            item = InvoiceItem(
                id=new_id("iitem_"),
                invoice_id=inv.id,
                organization_id=org_id,
                description=f"{plan_key} subscription ({cycle})",
                quantity=1,
                unit_price_usd=subtotal,
                amount_usd=subtotal,
            )
            store.save_item(item)
            tax_result = self.tax.calculate(
                organization_id=org_id,
                taxable_usd=taxable,
                country=country,
                invoice_id=inv.id,
                persist=True,
            )
            _emit(
                org_id,
                "invoice.generated",
                inv.invoice_number,
                actor_id=actor_id,
                status=status,
                totalUsd=total,
            )
            _audit(
                "billing.invoice.generated",
                actor_id,
                inv.invoice_number,
                organizationId=org_id,
            )
            return {
                "ok": True,
                "invoice": inv.to_dict(),
                "items": [item.to_dict()],
                "tax": tax_result["tax"],
            }

    def list(
        self, *, actor_id: str, organization_id: str, limit: int = 100
    ) -> dict[str, Any]:
        _require_read(actor_id=actor_id, organization_id=organization_id)
        items = store.list_invoices(organization_id, limit=limit)
        return {
            "ok": True,
            "organizationId": organization_id,
            "count": len(items),
            "invoices": [i.to_dict() for i in items],
        }

    def get(self, *, actor_id: str, invoice_id: str) -> dict[str, Any]:
        _, NotFoundError = _auth_errors()
        inv = store.get_invoice(invoice_id)
        if inv is None:
            raise NotFoundError("invoice not found")
        _require_read(actor_id=actor_id, organization_id=inv.organization_id)
        items = store.list_items(inv.id)
        return {
            "ok": True,
            "invoice": inv.to_dict(),
            "items": [i.to_dict() for i in items],
        }

    def mark_status(
        self, invoice_id: str, status: str, *, actor_id: str
    ) -> dict[str, Any]:
        ValidationError, _ = _validation()
        _, NotFoundError = _auth_errors()
        inv = store.get_invoice(invoice_id)
        if inv is None:
            raise NotFoundError("invoice not found")
        _require_manage(actor_id=actor_id, organization_id=inv.organization_id)
        if status not in {"pending", "paid", "failed", "refunded", "void", "draft"}:
            raise ValidationError(f"invalid invoice status: {status}")
        inv.status = status
        inv.updated_at = _now()
        if status == "paid":
            inv.paid_at = _now()
            if not inv.receipt_number:
                inv.receipt_number = (
                    f"RCT-{_now().strftime('%Y%m%d')}-{store.next_invoice_seq():05d}"
                )
        store.save_invoice(inv)
        _emit(
            inv.organization_id,
            f"invoice.{status}",
            inv.invoice_number,
            actor_id=actor_id,
        )
        return {"ok": True, "invoice": inv.to_dict()}


class PaymentRetryEngine:
    def __init__(self) -> None:
        self.invoices = InvoiceEngine()

    def schedule(
        self, invoice_id: str, *, actor_id: str, force_fail: bool = False
    ) -> dict[str, Any]:
        _, NotFoundError = _auth_errors()
        inv = store.get_invoice(invoice_id)
        if inv is None:
            raise NotFoundError("invoice not found")
        _require_manage(actor_id=actor_id, organization_id=inv.organization_id)
        if inv.status == "paid":
            return {"ok": True, "skipped": True, "reason": "already_paid"}
        inv.status = "failed"
        inv.updated_at = _now()
        store.save_invoice(inv)
        existing = store.get_retry_by_invoice(invoice_id)
        if existing and existing.status in {"scheduled", "processing"}:
            retry = existing
        else:
            retry = PaymentRetry(
                id=new_id("pretry_"),
                organization_id=inv.organization_id,
                invoice_id=inv.id,
                attempt=0,
                max_attempts=MAX_PAYMENT_RETRIES,
                status="scheduled",
                next_retry_at=_now() + timedelta(hours=RETRY_SCHEDULE_HOURS[0]),
                actor_id=actor_id,
            )
            store.save_retry(retry)
        _emit(
            inv.organization_id,
            "payment.retry_scheduled",
            inv.invoice_number,
            actor_id=actor_id,
        )
        return self.process(
            {"invoiceId": invoice_id, "forceFail": force_fail},
            actor_id=actor_id,
        )

    def process(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            _, NotFoundError = _auth_errors()
            invoice_id = require_non_empty(
                payload.get("invoiceId") or payload.get("invoice_id"),
                "invoiceId",
            )
            inv = store.get_invoice(invoice_id)
            if inv is None:
                raise NotFoundError("invoice not found")
            _require_manage(actor_id=actor_id, organization_id=inv.organization_id)
            retry = store.get_retry_by_invoice(invoice_id)
            if retry is None:
                retry = PaymentRetry(
                    id=new_id("pretry_"),
                    organization_id=inv.organization_id,
                    invoice_id=inv.id,
                    max_attempts=MAX_PAYMENT_RETRIES,
                    actor_id=actor_id,
                )
            if retry.status == "exhausted":
                raise ValidationError("payment retries exhausted")
            if inv.status == "paid":
                retry.status = "succeeded"
                store.save_retry(retry)
                return {"ok": True, "invoice": inv.to_dict(), "retry": retry.to_dict()}

            retry.attempt += 1
            retry.status = "processing"
            retry.updated_at = _now()
            force_fail = bool(payload.get("forceFail"))
            succeed = not force_fail and retry.attempt >= 1 and (
                payload.get("succeed") is not False
            )
            # Default path: succeed on first non-forced attempt (simulated capture)
            if force_fail:
                succeed = False
            if payload.get("succeed") is True:
                succeed = True

            if succeed:
                inv.status = "paid"
                inv.paid_at = _now()
                inv.receipt_number = (
                    inv.receipt_number
                    or f"RCT-{_now().strftime('%Y%m%d')}-{store.next_invoice_seq():05d}"
                )
                inv.updated_at = _now()
                store.save_invoice(inv)
                retry.status = "succeeded"
                retry.last_error = ""
                store.save_retry(retry)
                _emit(
                    inv.organization_id,
                    "payment.retry_succeeded",
                    inv.invoice_number,
                    actor_id=actor_id,
                    attempt=retry.attempt,
                )
                _audit(
                    "billing.payment.retry_succeeded",
                    actor_id,
                    inv.invoice_number,
                    organizationId=inv.organization_id,
                )
                return {
                    "ok": True,
                    "invoice": inv.to_dict(),
                    "retry": retry.to_dict(),
                    "receiptNumber": inv.receipt_number,
                }

            # Failed attempt
            retry.last_error = str(payload.get("error") or "payment_declined")
            if retry.attempt >= retry.max_attempts:
                retry.status = "exhausted"
                inv.status = "failed"
                store.save_invoice(inv)
                _emit(
                    inv.organization_id,
                    "payment.retry_exhausted",
                    inv.invoice_number,
                    actor_id=actor_id,
                )
            else:
                delay = RETRY_SCHEDULE_HOURS[
                    min(retry.attempt, len(RETRY_SCHEDULE_HOURS) - 1)
                ]
                retry.status = "scheduled"
                retry.next_retry_at = _now() + timedelta(hours=delay)
                inv.status = "failed"
                store.save_invoice(inv)
                _emit(
                    inv.organization_id,
                    "payment.retry_failed",
                    inv.invoice_number,
                    actor_id=actor_id,
                    attempt=retry.attempt,
                )
            retry.updated_at = _now()
            store.save_retry(retry)
            return {
                "ok": True,
                "invoice": inv.to_dict(),
                "retry": retry.to_dict(),
                "succeeded": False,
            }


class BillingAutomationEngine:
    def __init__(self) -> None:
        self.invoices = InvoiceEngine()
        self.retries = PaymentRetryEngine()

    def renew(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        """Automatic renewal: generate invoice + optional auto-pay."""
        ValidationError, require_non_empty = _validation()
        org_id = require_non_empty(
            payload.get("organizationId") or payload.get("organization_id"),
            "organizationId",
        )
        _require_manage(actor_id=actor_id, organization_id=org_id)
        plan_key = str(payload.get("planKey") or "starter")
        cycle = str(payload.get("billingCycle") or "monthly")
        auto_pay = bool(payload.get("autoPay", True))
        generated = self.invoices.generate(
            {
                "organizationId": org_id,
                "planKey": plan_key,
                "billingCycle": cycle,
                "country": payload.get("country"),
                "couponCode": payload.get("couponCode"),
                "status": "pending",
            },
            actor_id=actor_id,
        )
        inv = generated["invoice"]
        _emit(org_id, "subscription.renewal", inv["invoiceNumber"], actor_id=actor_id)
        result: dict[str, Any] = {
            "ok": True,
            "renewal": True,
            "invoice": inv,
            "items": generated["items"],
        }
        if auto_pay and float(inv["totalUsd"]) >= 0:
            paid = self.invoices.mark_status(inv["id"], "paid", actor_id=actor_id)
            result["invoice"] = paid["invoice"]
            result["receiptNumber"] = paid["invoice"].get("receiptNumber")
            _emit(org_id, "receipt.generated", result["receiptNumber"] or "", actor_id=actor_id)
        return result

    def remind(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        ValidationError, require_non_empty = _validation()
        org_id = require_non_empty(
            payload.get("organizationId") or payload.get("organization_id"),
            "organizationId",
        )
        _require_manage(actor_id=actor_id, organization_id=org_id)
        days = int(payload.get("daysBefore") or REMINDER_DAYS_BEFORE_RENEWAL[0])
        event = _emit(
            org_id,
            "subscription.reminder",
            f"renewal reminder {days}d",
            actor_id=actor_id,
            daysBefore=days,
        )
        return {"ok": True, "reminder": event.to_dict()}

    def expire_subscription(
        self, payload: dict[str, Any], *, actor_id: str
    ) -> dict[str, Any]:
        ValidationError, require_non_empty = _validation()
        org_id = require_non_empty(
            payload.get("organizationId") or payload.get("organization_id"),
            "organizationId",
        )
        _require_manage(actor_id=actor_id, organization_id=org_id)
        try:
            from app.services.billing import store as billing_store

            sub = billing_store.get_org_subscription_by_org(org_id)
            if sub is not None:
                sub.status = "expired"
                sub.updated_at = _now()
                billing_store.save_org_subscription(sub)
        except Exception:
            pass
        event = _emit(
            org_id,
            "subscription.expired",
            "subscription expired",
            actor_id=actor_id,
        )
        return {"ok": True, "expired": True, "event": event.to_dict()}


class BillingAutomationService:
    def __init__(self) -> None:
        self.invoices = InvoiceEngine()
        self.tax = TaxEngine()
        self.coupons = CouponEngine()
        self.discounts = DiscountEngine()
        self.automation = BillingAutomationEngine()
        self.retries = PaymentRetryEngine()
        self.coupons.ensure_defaults()

    def status(self) -> dict[str, Any]:
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "label": ENGINE_LABEL,
            "phase": PHASE,
            "sprint": SPRINT,
            "engines": {
                "invoice": "ready",
                "tax": "ready",
                "coupon": "ready",
                "discount": "ready",
                "automation": "ready",
                "paymentRetry": "ready",
            },
            "stats": store.metrics_snapshot(),
        }


_service: BillingAutomationService | None = None


def get_billing_automation_service() -> BillingAutomationService:
    global _service
    if _service is None:
        _service = BillingAutomationService()
    return _service


def reset_engine() -> None:
    global _service
    store.reset_store()
    try:
        from app.services.billing.service import reset_engine as reset_billing
        from app.services.enterprise_auth.engine import reset_engine as reset_ea
        from app.services.multi_tenant.engine import reset_engine as reset_mt

        reset_billing()
        reset_mt()
        reset_ea()
    except Exception:
        pass
    _service = None


get_engine = get_billing_automation_service
