"""Paddle Billing Integration Engine — Phase 8 Sprint 2."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from app.services.billing.catalog import normalize_cycle, normalize_plan_key
from app.services.enterprise_auth.audit import log_auth_event
from app.services.enterprise_auth.errors import ForbiddenError, NotFoundError
from app.services.enterprise_auth.middleware import require_access
from app.services.multi_tenant.repository import get_repository
from app.services.multi_tenant.validation import ValidationError, require_non_empty
from app.services.paddle_billing import store
from app.services.paddle_billing.catalog import (
    WEBHOOK_EVENTS,
    plan_key_from_price_id,
    product_catalog,
    resolve_price_id,
)
from app.services.paddle_billing.models import (
    BillingEvent,
    CheckoutSession,
    PaddleCustomer,
    PaddleSubscription,
    PaddleTransaction,
    PaddleWebhookLog,
    new_id,
)
from app.services.paddle_billing.signatures import SignatureError, verify_paddle_signature
from app.services.paddle_billing.version import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    PHASE,
    SPRINT,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _audit(action: str, actor_id: str, detail: str | None = None, **meta: Any) -> None:
    log_auth_event(
        action,
        actor_id=actor_id,
        success=True,
        detail=detail or action,
        metadata=meta,
    )


def _require_manage(*, actor_id: str, organization_id: str) -> None:
    require_access(
        user_id=actor_id,
        organization_id=organization_id,
        permission="org.update",
    )
    member = get_repository().get_member_by_org_user(organization_id, actor_id)
    if member is None or member.role_key not in {"owner", "admin", "manager"}:
        raise ForbiddenError("billing ownership denied")


def _require_read(*, actor_id: str, organization_id: str) -> None:
    require_access(
        user_id=actor_id,
        organization_id=organization_id,
        permission="org.read",
    )


def _record_event(
    organization_id: str,
    event_type: str,
    *,
    actor_id: str | None = None,
    detail: str = "",
    metadata: dict[str, Any] | None = None,
) -> BillingEvent:
    ev = BillingEvent(
        id=new_id("bevt_"),
        organization_id=organization_id,
        event_type=event_type,
        actor_id=actor_id,
        detail=detail,
        metadata=dict(metadata or {}),
    )
    store.save_event(ev)
    return ev


def _sync_internal_subscription(
    *,
    organization_id: str,
    plan_key: str,
    billing_cycle: str,
    status: str,
    actor_id: str = "paddle_webhook",
    cancel_at_period_end: bool = False,
) -> None:
    """Keep Sprint 1 billing foundation in sync with Paddle state."""
    try:
        from app.services.billing.service import get_billing_service
        from app.services.billing import store as billing_store

        svc = get_billing_service()
        existing = billing_store.get_org_subscription_by_org(organization_id)
        if existing is None:
            # Create via manage path may fail without actor membership — write via update helper
            try:
                svc.subscriptions.create(
                    {
                        "organizationId": organization_id,
                        "planKey": plan_key,
                        "billingCycle": billing_cycle,
                    },
                    actor_id=actor_id if actor_id != "paddle_webhook" else "system",
                )
            except Exception:
                # Fallback: ensure wallet + synthetic create via store using owner of org
                org = get_repository().get_organization(organization_id)
                owner = org.owner_id if org else "system"
                if billing_store.get_org_subscription_by_org(organization_id) is None:
                    svc.subscriptions.create(
                        {
                            "organizationId": organization_id,
                            "planKey": plan_key,
                            "billingCycle": billing_cycle,
                        },
                        actor_id=owner,
                    )
            existing = billing_store.get_org_subscription_by_org(organization_id)
        if existing:
            payload: dict[str, Any] = {
                "organizationId": organization_id,
                "planKey": plan_key,
                "billingCycle": billing_cycle,
                "status": status,
                "cancelAtPeriodEnd": cancel_at_period_end,
            }
            org = get_repository().get_organization(organization_id)
            owner = org.owner_id if org else actor_id
            try:
                svc.subscriptions.update(payload, actor_id=owner)
            except Exception:
                existing.plan_key = plan_key
                existing.billing_cycle = billing_cycle
                existing.status = status
                existing.cancel_at_period_end = cancel_at_period_end
                existing.updated_at = _now()
                billing_store.save_org_subscription(existing)
    except Exception:
        # Sync is best-effort — Paddle state remains source of truth in this package
        pass


class ProductPriceManager:
    def list_products(self) -> dict[str, Any]:
        return {"ok": True, "products": product_catalog()}

    def price_for(self, plan_key: str, billing_cycle: str) -> str:
        return resolve_price_id(normalize_plan_key(plan_key), normalize_cycle(billing_cycle))


class CustomerManager:
    def ensure(
        self,
        *,
        organization_id: str,
        email: str,
        name: str = "",
        country_code: str = "",
        actor_id: str | None = None,
        tax_identifier: str | None = None,
        address: dict[str, Any] | None = None,
        paddle_customer_id: str | None = None,
    ) -> PaddleCustomer:
        existing = store.get_customer_by_org(organization_id)
        address = address or {}
        if existing:
            existing.email = email or existing.email
            existing.name = name or existing.name
            if country_code:
                existing.country_code = country_code.upper()[:2]
            if tax_identifier is not None:
                existing.tax_identifier = tax_identifier
            if paddle_customer_id:
                existing.paddle_customer_id = paddle_customer_id
            existing.address_line1 = address.get("line1") or existing.address_line1
            existing.address_line2 = address.get("line2") or existing.address_line2
            existing.city = address.get("city") or existing.city
            existing.region = address.get("region") or existing.region
            existing.postal_code = address.get("postalCode") or existing.postal_code
            existing.updated_at = _now()
            store.save_customer(existing)
            if actor_id:
                _audit(
                    "paddle.customer.updated",
                    actor_id,
                    existing.paddle_customer_id,
                    organizationId=organization_id,
                )
            return existing

        paddle_id = paddle_customer_id or f"ctm_{uuid4().hex[:24]}"
        customer = PaddleCustomer(
            id=new_id("pcust_"),
            organization_id=organization_id,
            paddle_customer_id=paddle_id,
            email=email,
            name=name,
            country_code=(country_code or "").upper()[:2],
            tax_identifier=tax_identifier,
            address_line1=address.get("line1"),
            address_line2=address.get("line2"),
            city=address.get("city"),
            region=address.get("region"),
            postal_code=address.get("postalCode"),
        )
        store.save_customer(customer)
        _record_event(
            organization_id,
            "customer.created",
            actor_id=actor_id,
            detail=paddle_id,
        )
        if actor_id:
            _audit(
                "paddle.customer.created",
                actor_id,
                paddle_id,
                organizationId=organization_id,
            )
        return customer

    def get(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        _require_read(actor_id=actor_id, organization_id=organization_id)
        customer = store.get_customer_by_org(organization_id)
        return {
            "ok": True,
            "organizationId": organization_id,
            "customer": customer.to_dict() if customer else None,
        }

    def update(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        org_id = require_non_empty(
            payload.get("organizationId") or payload.get("organization_id"),
            "organizationId",
        )
        _require_manage(actor_id=actor_id, organization_id=org_id)
        customer = self.ensure(
            organization_id=org_id,
            email=str(payload.get("email") or ""),
            name=str(payload.get("name") or ""),
            country_code=str(payload.get("countryCode") or payload.get("country") or ""),
            actor_id=actor_id,
            tax_identifier=payload.get("taxIdentifier") or payload.get("taxId"),
            address=payload.get("address") or {},
        )
        return {"ok": True, "customer": customer.to_dict()}


class CheckoutSessionManager:
    def __init__(self) -> None:
        self.customers = CustomerManager()
        self.products = ProductPriceManager()

    def create(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            org_id = require_non_empty(
                payload.get("organizationId") or payload.get("organization_id"),
                "organizationId",
            )
            _require_manage(actor_id=actor_id, organization_id=org_id)
            if get_repository().get_organization(org_id) is None:
                raise NotFoundError("organization not found")

            plan_key = normalize_plan_key(
                str(payload.get("planKey") or payload.get("plan") or "starter")
            )
            cycle = normalize_cycle(
                str(payload.get("billingCycle") or payload.get("cycle") or "monthly")
            )
            email = str(
                payload.get("email")
                or payload.get("billingEmail")
                or f"{actor_id}@rtas.local"
            )
            country = str(
                payload.get("countryCode")
                or payload.get("country")
                or self._detect_country(payload)
            )
            customer = self.customers.ensure(
                organization_id=org_id,
                email=email,
                name=str(payload.get("name") or payload.get("companyName") or ""),
                country_code=country,
                actor_id=actor_id,
                tax_identifier=payload.get("taxIdentifier") or payload.get("taxId"),
                address=payload.get("address") or {},
            )
            price_id = self.products.price_for(plan_key, cycle)
            success_url = payload.get("successUrl") or payload.get("success_url")
            cancel_url = payload.get("cancelUrl") or payload.get("cancel_url")
            checkout_id = new_id("chk_")
            base = (
                os.environ.get("NEXT_PUBLIC_PADDLE_CHECKOUT_URL")
                or "https://checkout.paddle.com"
            ).rstrip("/")
            checkout_url = (
                f"{base}/?price_id={price_id}"
                f"&customer_id={customer.paddle_customer_id}"
                f"&custom_data[organization_id]={org_id}"
                f"&custom_data[plan_key]={plan_key}"
                f"&custom_data[billing_cycle]={cycle}"
                f"&_rtas_session={checkout_id}"
            )
            session = CheckoutSession(
                id=checkout_id,
                organization_id=org_id,
                plan_key=plan_key,
                billing_cycle=cycle,
                price_id=price_id,
                customer_id=customer.paddle_customer_id,
                checkout_url=checkout_url,
                actor_id=actor_id,
                success_url=str(success_url) if success_url else None,
                cancel_url=str(cancel_url) if cancel_url else None,
                metadata={"trial": plan_key == "free_trial"},
            )
            store.save_checkout(session)
            _record_event(
                org_id,
                "checkout.created",
                actor_id=actor_id,
                detail=checkout_id,
                metadata={"planKey": plan_key, "cycle": cycle},
            )
            _audit(
                "paddle.checkout.created",
                actor_id,
                checkout_id,
                organizationId=org_id,
                planKey=plan_key,
            )
            return {
                "ok": True,
                "checkout": session.to_dict(),
                "customer": customer.to_dict(),
                "provider": "paddle",
            }

    def _detect_country(self, payload: dict[str, Any]) -> str:
        for key in ("cf-ipcountry", "x-vercel-ip-country", "country"):
            val = payload.get(key)
            if isinstance(val, str) and len(val.strip()) == 2:
                return val.strip().upper()
        return "US"


class SubscriptionSyncEngine:
    def status(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        _require_read(actor_id=actor_id, organization_id=organization_id)
        sub = store.get_subscription_by_org(organization_id)
        customer = store.get_customer_by_org(organization_id)
        return {
            "ok": True,
            "organizationId": organization_id,
            "provider": "paddle",
            "subscription": sub.to_dict() if sub else None,
            "customer": customer.to_dict() if customer else None,
            "status": sub.status if sub else "none",
            "hasActiveSubscription": bool(
                sub and sub.status in {"active", "trialing", "past_due"}
            ),
        }

    def upsert_from_paddle(
        self,
        *,
        organization_id: str,
        paddle_subscription_id: str,
        paddle_customer_id: str,
        plan_key: str,
        billing_cycle: str,
        status: str,
        price_id: str | None = None,
        cancel_at_period_end: bool = False,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> PaddleSubscription:
        sub = store.get_subscription_by_paddle(paddle_subscription_id) or store.get_subscription_by_org(
            organization_id
        )
        now = _now()
        if sub is None:
            sub = PaddleSubscription(
                id=new_id("psub_"),
                organization_id=organization_id,
                paddle_subscription_id=paddle_subscription_id,
                paddle_customer_id=paddle_customer_id,
                plan_key=plan_key,
                billing_cycle=billing_cycle,
                status=status,
                price_id=price_id,
                cancel_at_period_end=cancel_at_period_end,
                current_period_start=period_start or now,
                current_period_end=period_end or now + timedelta(days=30),
            )
        else:
            sub.paddle_subscription_id = paddle_subscription_id
            sub.paddle_customer_id = paddle_customer_id
            sub.plan_key = plan_key
            sub.billing_cycle = billing_cycle
            sub.status = status
            sub.price_id = price_id or sub.price_id
            sub.cancel_at_period_end = cancel_at_period_end
            if period_start:
                sub.current_period_start = period_start
            if period_end:
                sub.current_period_end = period_end
            sub.updated_at = now
        store.save_subscription(sub)
        _sync_internal_subscription(
            organization_id=organization_id,
            plan_key=plan_key,
            billing_cycle=billing_cycle,
            status=status,
            cancel_at_period_end=cancel_at_period_end,
        )
        return sub

    def cancel(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            org_id = require_non_empty(
                payload.get("organizationId") or payload.get("organization_id"),
                "organizationId",
            )
            _require_manage(actor_id=actor_id, organization_id=org_id)
            sub = store.get_subscription_by_org(org_id)
            if sub is None:
                raise NotFoundError("paddle subscription not found")
            immediate = bool(payload.get("immediate") or payload.get("effectiveImmediately"))
            if immediate:
                sub.status = "canceled"
                sub.cancel_at_period_end = False
            else:
                sub.cancel_at_period_end = True
                sub.status = "active"
            sub.updated_at = _now()
            store.save_subscription(sub)
            _sync_internal_subscription(
                organization_id=org_id,
                plan_key=sub.plan_key,
                billing_cycle=sub.billing_cycle,
                status="canceled" if immediate else sub.status,
                actor_id=actor_id,
                cancel_at_period_end=sub.cancel_at_period_end,
            )
            _record_event(
                org_id,
                "subscription.canceled" if immediate else "subscription.cancel_scheduled",
                actor_id=actor_id,
                detail=sub.paddle_subscription_id,
            )
            _audit(
                "paddle.subscription.cancel",
                actor_id,
                sub.paddle_subscription_id,
                organizationId=org_id,
            )
            return {"ok": True, "subscription": sub.to_dict()}

    def resume(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            org_id = require_non_empty(
                payload.get("organizationId") or payload.get("organization_id"),
                "organizationId",
            )
            _require_manage(actor_id=actor_id, organization_id=org_id)
            sub = store.get_subscription_by_org(org_id)
            if sub is None:
                raise NotFoundError("paddle subscription not found")
            sub.status = "active"
            sub.cancel_at_period_end = False
            sub.updated_at = _now()
            store.save_subscription(sub)
            _sync_internal_subscription(
                organization_id=org_id,
                plan_key=sub.plan_key,
                billing_cycle=sub.billing_cycle,
                status="active",
                actor_id=actor_id,
                cancel_at_period_end=False,
            )
            _record_event(
                org_id,
                "subscription.resumed",
                actor_id=actor_id,
                detail=sub.paddle_subscription_id,
            )
            _audit(
                "paddle.subscription.resume",
                actor_id,
                sub.paddle_subscription_id,
                organizationId=org_id,
            )
            return {"ok": True, "subscription": sub.to_dict()}


class WebhookProcessingEngine:
    def __init__(self) -> None:
        self.sync = SubscriptionSyncEngine()
        self.customers = CustomerManager()

    def process(
        self,
        *,
        raw_body: bytes | str,
        signature_header: str | None,
        allow_unsigned: bool = False,
    ) -> dict[str, Any]:
        with store.timed_op():
            try:
                verify_paddle_signature(
                    signature_header,
                    raw_body,
                    allow_unsigned_in_tests=allow_unsigned,
                )
                sig_ok = True
                sig_error = None
            except SignatureError as exc:
                sig_ok = False
                sig_error = str(exc)

            try:
                payload = json.loads(
                    raw_body.decode("utf-8") if isinstance(raw_body, bytes) else raw_body
                )
            except Exception as exc:
                raise ValidationError(f"invalid webhook JSON: {exc}") from exc

            event_type = str(
                payload.get("event_type")
                or payload.get("eventType")
                or (payload.get("data") or {}).get("event_type")
                or ""
            )
            event_id = str(
                payload.get("event_id")
                or payload.get("notification_id")
                or payload.get("eventId")
                or new_id("evt_")
            )
            data = payload.get("data") if isinstance(payload.get("data"), dict) else payload

            log = PaddleWebhookLog(
                id=new_id("pwh_"),
                event_id=event_id,
                event_type=event_type or "unknown",
                signature_valid=sig_ok,
                payload=payload if isinstance(payload, dict) else {},
                error=sig_error,
            )
            store.save_webhook(log)

            if not sig_ok:
                raise SignatureError(sig_error or "invalid signature")

            if not store.mark_event_processed(event_id):
                return {
                    "ok": True,
                    "duplicate": True,
                    "eventId": event_id,
                    "eventType": event_type,
                }

            result = self._dispatch(event_type, data if isinstance(data, dict) else {})
            log.processed = True
            log.organization_id = result.get("organizationId")
            store.save_webhook(log)
            return {
                "ok": True,
                "eventId": event_id,
                "eventType": event_type,
                "supported": event_type in WEBHOOK_EVENTS or event_type.replace("cancelled", "canceled") in WEBHOOK_EVENTS,
                **result,
            }

    def _org_from_custom(self, data: dict[str, Any]) -> str | None:
        custom = data.get("custom_data") or data.get("customData") or {}
        if isinstance(custom, dict):
            return custom.get("organization_id") or custom.get("organizationId")
        return None

    def _dispatch(self, event_type: str, data: dict[str, Any]) -> dict[str, Any]:
        et = event_type.replace("cancelled", "canceled")
        org_id = self._org_from_custom(data)
        customer_id = str(
            data.get("customer_id")
            or data.get("customerId")
            or (data.get("customer") or {}).get("id")
            or ""
        )
        if not org_id and customer_id:
            cust = store.get_customer_by_paddle(customer_id)
            if cust:
                org_id = cust.organization_id

        if et in {"subscription.created", "subscription.updated", "subscription.resumed"}:
            return self._handle_subscription(et, data, org_id, customer_id)
        if et == "subscription.canceled":
            return self._handle_subscription(et, data, org_id, customer_id, force_status="canceled")
        if et in {"transaction.completed", "payment.succeeded"}:
            return self._handle_transaction(et, data, org_id, customer_id, status="completed")
        if et == "payment.failed":
            return self._handle_payment_failed(data, org_id, customer_id)
        if et in {"refund.created", "refund.completed"}:
            return self._handle_refund(et, data, org_id, customer_id)
        _record_event(org_id or "unknown", et or "unknown", detail="unhandled_or_info")
        return {"organizationId": org_id, "handled": False}

    def _handle_subscription(
        self,
        event_type: str,
        data: dict[str, Any],
        org_id: str | None,
        customer_id: str,
        *,
        force_status: str | None = None,
    ) -> dict[str, Any]:
        if not org_id:
            raise ValidationError("organization_id missing in webhook custom_data")
        sub_id = str(data.get("id") or data.get("subscription_id") or new_id("sub_"))
        items = data.get("items") or []
        price_id = None
        if items and isinstance(items, list):
            price = (items[0] or {}).get("price") or {}
            price_id = price.get("id")
        price_id = price_id or data.get("price_id") or data.get("priceId")
        plan_key = (
            plan_key_from_price_id(str(price_id or ""))
            or self._org_plan_from_custom(data)
            or "starter"
        )
        cycle = "yearly" if "year" in str(price_id or "").lower() else "monthly"
        custom = data.get("custom_data") or {}
        if isinstance(custom, dict) and custom.get("billing_cycle"):
            cycle = normalize_cycle(str(custom["billing_cycle"]))
        status = force_status or str(data.get("status") or "active").lower()
        if status == "cancelled":
            status = "canceled"
        if event_type == "subscription.resumed":
            status = "active"
        sub = self.sync.upsert_from_paddle(
            organization_id=org_id,
            paddle_subscription_id=sub_id,
            paddle_customer_id=customer_id or "ctm_unknown",
            plan_key=plan_key,
            billing_cycle=cycle,
            status=status,
            price_id=str(price_id) if price_id else None,
            cancel_at_period_end=bool(data.get("scheduled_change")),
        )
        if customer_id:
            self.customers.ensure(
                organization_id=org_id,
                email=str(
                    (data.get("customer") or {}).get("email")
                    or f"billing@{org_id}.local"
                ),
                name="",
                paddle_customer_id=customer_id,
            )
        _record_event(org_id, event_type, detail=sub_id, metadata={"planKey": plan_key})
        return {
            "organizationId": org_id,
            "handled": True,
            "subscription": sub.to_dict(),
        }

    def _org_plan_from_custom(self, data: dict[str, Any]) -> str | None:
        custom = data.get("custom_data") or data.get("customData") or {}
        if isinstance(custom, dict) and custom.get("plan_key"):
            try:
                return normalize_plan_key(str(custom["plan_key"]))
            except Exception:
                return None
        return None

    def _handle_transaction(
        self,
        event_type: str,
        data: dict[str, Any],
        org_id: str | None,
        customer_id: str,
        *,
        status: str,
    ) -> dict[str, Any]:
        if not org_id:
            # Allow transaction without org — log only
            org_id = "unknown"
        txn_id = str(data.get("id") or data.get("transaction_id") or new_id("txn_"))
        details = data.get("details") or {}
        totals = details.get("totals") if isinstance(details, dict) else {}
        amount = 0.0
        if isinstance(totals, dict):
            # Paddle amounts often in minor units
            raw = totals.get("grand_total") or totals.get("total") or 0
            try:
                amount = float(raw) / 100.0 if float(raw) > 1000 else float(raw)
            except Exception:
                amount = 0.0
        txn = PaddleTransaction(
            id=new_id("ptxn_"),
            organization_id=org_id,
            paddle_transaction_id=txn_id,
            paddle_subscription_id=str(data.get("subscription_id") or "") or None,
            paddle_customer_id=customer_id or None,
            status=status,
            amount_usd=amount,
            event_type=event_type,
        )
        store.save_transaction(txn)
        _record_event(org_id, event_type, detail=txn_id, metadata={"amountUsd": amount})
        # Renewal / completed payment → ensure subscription active
        sub_id = data.get("subscription_id")
        if sub_id and org_id != "unknown":
            existing = store.get_subscription_by_paddle(str(sub_id))
            if existing:
                existing.status = "active"
                existing.updated_at = _now()
                store.save_subscription(existing)
                _sync_internal_subscription(
                    organization_id=org_id,
                    plan_key=existing.plan_key,
                    billing_cycle=existing.billing_cycle,
                    status="active",
                )
        return {"organizationId": org_id, "handled": True, "transaction": txn.to_dict()}

    def _handle_payment_failed(
        self, data: dict[str, Any], org_id: str | None, customer_id: str
    ) -> dict[str, Any]:
        if not org_id:
            raise ValidationError("organization_id missing for payment.failed")
        sub = store.get_subscription_by_org(org_id)
        if sub:
            sub.status = "past_due"
            sub.updated_at = _now()
            store.save_subscription(sub)
            _sync_internal_subscription(
                organization_id=org_id,
                plan_key=sub.plan_key,
                billing_cycle=sub.billing_cycle,
                status="past_due",
            )
        _record_event(org_id, "payment.failed", detail=customer_id)
        return {"organizationId": org_id, "handled": True, "status": "past_due"}

    def _handle_refund(
        self, event_type: str, data: dict[str, Any], org_id: str | None, customer_id: str
    ) -> dict[str, Any]:
        org_id = org_id or "unknown"
        txn_id = str(data.get("id") or data.get("refund_id") or new_id("ref_"))
        txn = PaddleTransaction(
            id=new_id("ptxn_"),
            organization_id=org_id,
            paddle_transaction_id=txn_id,
            paddle_customer_id=customer_id or None,
            status="refunded",
            event_type=event_type,
        )
        store.save_transaction(txn)
        _record_event(org_id, event_type, detail=txn_id)
        return {"organizationId": org_id, "handled": True, "transaction": txn.to_dict()}


class PaddleBillingEngine:
    def status(self) -> dict[str, Any]:
        secret = bool((os.environ.get("PADDLE_WEBHOOK_SECRET") or "").strip())
        api_key = bool((os.environ.get("PADDLE_API_KEY") or "").strip())
        m = store.metrics()
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "label": ENGINE_LABEL,
            "phase": PHASE,
            "sprint": SPRINT,
            "provider": "paddle",
            "webhookSecretConfigured": secret,
            "apiKeyConfigured": api_key,
            "engines": {
                "paddle": "ready",
                "checkout": "ready",
                "customers": "ready",
                "products": "ready",
                "subscriptions": "ready",
                "webhooks": "ready",
            },
            "supportedWebhookEvents": list(WEBHOOK_EVENTS),
            "stats": m,
        }

    def observability(self) -> dict[str, Any]:
        return {"ok": True, **store.metrics()}


class PaddleBillingService:
    def __init__(self) -> None:
        self.paddle = PaddleBillingEngine()
        self.products = ProductPriceManager()
        self.customers = CustomerManager()
        self.checkout = CheckoutSessionManager()
        self.subscriptions = SubscriptionSyncEngine()
        self.webhooks = WebhookProcessingEngine()

    def status(self) -> dict[str, Any]:
        return self.paddle.status()

    def observability(self) -> dict[str, Any]:
        return self.paddle.observability()


_service: PaddleBillingService | None = None


def get_paddle_billing_service() -> PaddleBillingService:
    global _service
    if _service is None:
        _service = PaddleBillingService()
    return _service


def reset_engine() -> None:
    global _service
    store.reset_store()
    try:
        from app.services.billing.service import reset_engine as reset_billing
        from app.services.multi_tenant.engine import reset_engine as reset_mt
        from app.services.enterprise_auth.engine import reset_engine as reset_ea

        reset_billing()
        reset_mt()
        reset_ea()
    except Exception:
        pass
    _service = None


get_engine = get_paddle_billing_service
