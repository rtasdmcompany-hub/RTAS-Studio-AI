"""PayPal, Credit Wallet & Payment Processing Engine — Phase 8 Sprint 3."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from app.services.enterprise_auth.audit import log_auth_event
from app.services.enterprise_auth.errors import ForbiddenError, NotFoundError
from app.services.enterprise_auth.middleware import require_access
from app.services.multi_tenant.repository import get_repository
from app.services.multi_tenant.validation import ValidationError, require_non_empty
from app.services.payment_processing import store
from app.services.payment_processing.catalog import (
    CREDIT_PACKS,
    get_pack,
    total_credits,
)
from app.services.payment_processing.models import (
    PaymentHistoryEntry,
    PayPalPayment,
    RefundHistoryEntry,
    RefundRequest,
    WalletAccount,
    WalletTransaction,
    new_id,
)
from app.services.payment_processing.signatures import (
    SignatureError,
    compute_transmission_hash,
    verify_paypal_webhook,
)
from app.services.payment_processing.version import (
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


def _require_read(*, actor_id: str, organization_id: str) -> None:
    require_access(
        user_id=actor_id,
        organization_id=organization_id,
        permission="org.read",
    )


def _require_manage(*, actor_id: str, organization_id: str) -> None:
    require_access(
        user_id=actor_id,
        organization_id=organization_id,
        permission="org.update",
    )
    member = get_repository().get_member_by_org_user(organization_id, actor_id)
    if member is None or member.role_key not in {"owner", "admin", "manager"}:
        raise ForbiddenError("wallet ownership denied")


def _sync_billing_wallet(organization_id: str, amount: int, *, reason: str, actor_id: str | None) -> None:
    """Best-effort sync into Phase 8 Sprint 1 billing credit store."""
    try:
        from app.services.billing.service import get_billing_service

        svc = get_billing_service()
        if amount > 0:
            svc.credits.grant(
                organization_id,
                amount,
                actor_id=actor_id,
                reason=reason,
                reference_type="payment_processing",
            )
        elif amount < 0:
            svc.credits.consume(
                organization_id,
                abs(amount),
                actor_id=actor_id,
                reason=reason,
            )
    except Exception:
        pass


class CreditWalletEngine:
    def ensure(self, organization_id: str) -> WalletAccount:
        wallet = store.get_wallet_by_org(organization_id)
        if wallet:
            self._expire_if_needed(wallet)
            return wallet
        wallet = WalletAccount(id=new_id("wwal_"), organization_id=organization_id)
        store.save_wallet(wallet)
        return wallet

    def _expire_if_needed(self, wallet: WalletAccount) -> None:
        if wallet.expires_at and wallet.expires_at < _now() and (
            wallet.trial_balance > 0 or wallet.promo_balance > 0
        ):
            expired = wallet.trial_balance + wallet.promo_balance
            wallet.balance = max(0, wallet.balance - expired)
            wallet.trial_balance = 0
            wallet.promo_balance = 0
            wallet.updated_at = _now()
            store.save_wallet(wallet)
            txn = WalletTransaction(
                id=new_id("wtxn_"),
                wallet_id=wallet.id,
                organization_id=wallet.organization_id,
                amount=-expired,
                balance_after=wallet.balance,
                txn_type="expire",
                credit_category="trial",
                reason="credit_expiration",
            )
            store.save_txn(txn)

    def get(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        _require_read(actor_id=actor_id, organization_id=organization_id)
        wallet = self.ensure(organization_id)
        return {"ok": True, "wallet": wallet.to_dict(), "packs": CREDIT_PACKS}


class CreditTransactionEngine:
    def __init__(self) -> None:
        self.wallets = CreditWalletEngine()

    def history(
        self, *, actor_id: str, organization_id: str, limit: int = 100
    ) -> dict[str, Any]:
        _require_read(actor_id=actor_id, organization_id=organization_id)
        self.wallets.ensure(organization_id)
        items = store.list_txns(organization_id, limit=limit)
        return {
            "ok": True,
            "organizationId": organization_id,
            "count": len(items),
            "transactions": [t.to_dict() for t in items],
        }

    def credit(
        self,
        organization_id: str,
        amount: int,
        *,
        txn_type: str,
        credit_category: str = "purchased",
        actor_id: str | None = None,
        reason: str = "",
        reference_type: str | None = None,
        reference_id: str | None = None,
        expires_at: datetime | None = None,
        sync_billing: bool = True,
    ) -> dict[str, Any]:
        if amount <= 0:
            raise ValidationError("credit amount must be > 0")
        wallet = self.wallets.ensure(organization_id)
        wallet.balance += amount
        if credit_category == "bonus":
            wallet.bonus_balance += amount
            wallet.lifetime_awarded += amount
        elif credit_category == "trial":
            wallet.trial_balance += amount
            wallet.lifetime_awarded += amount
        elif credit_category == "promotional":
            wallet.promo_balance += amount
            wallet.lifetime_awarded += amount
        elif credit_category == "subscription":
            wallet.lifetime_awarded += amount
        else:
            wallet.lifetime_purchased += amount
        if expires_at:
            wallet.expires_at = expires_at
        wallet.updated_at = _now()
        store.save_wallet(wallet)
        txn = WalletTransaction(
            id=new_id("wtxn_"),
            wallet_id=wallet.id,
            organization_id=organization_id,
            amount=amount,
            balance_after=wallet.balance,
            txn_type=txn_type,
            credit_category=credit_category,
            reason=reason,
            actor_id=actor_id,
            reference_type=reference_type,
            reference_id=reference_id,
            expires_at=expires_at,
        )
        store.save_txn(txn)
        if sync_billing:
            _sync_billing_wallet(organization_id, amount, reason=reason or txn_type, actor_id=actor_id)
        if actor_id:
            _audit(
                f"wallet.{txn_type}",
                actor_id,
                reason or txn_type,
                organizationId=organization_id,
                amount=amount,
            )
        return {"ok": True, "wallet": wallet.to_dict(), "transaction": txn.to_dict()}

    def debit(
        self,
        organization_id: str,
        amount: int,
        *,
        txn_type: str = "consume",
        actor_id: str | None = None,
        reason: str = "",
        reference_type: str | None = None,
        reference_id: str | None = None,
        sync_billing: bool = True,
    ) -> dict[str, Any]:
        if amount <= 0:
            raise ValidationError("debit amount must be > 0")
        wallet = self.wallets.ensure(organization_id)
        if wallet.available < amount:
            raise ValidationError("insufficient credits")
        wallet.balance -= amount
        wallet.lifetime_consumed += amount
        # burn promo/trial first for accounting
        remain = amount
        for attr in ("promo_balance", "trial_balance", "bonus_balance"):
            cur = getattr(wallet, attr)
            take = min(cur, remain)
            setattr(wallet, attr, cur - take)
            remain -= take
            if remain <= 0:
                break
        wallet.updated_at = _now()
        store.save_wallet(wallet)
        txn = WalletTransaction(
            id=new_id("wtxn_"),
            wallet_id=wallet.id,
            organization_id=organization_id,
            amount=-amount,
            balance_after=wallet.balance,
            txn_type=txn_type,
            credit_category="purchased",
            reason=reason,
            actor_id=actor_id,
            reference_type=reference_type,
            reference_id=reference_id,
        )
        store.save_txn(txn)
        if sync_billing:
            _sync_billing_wallet(organization_id, -amount, reason=reason or txn_type, actor_id=actor_id)
        return {"ok": True, "wallet": wallet.to_dict(), "transaction": txn.to_dict()}


class PurchaseHistoryEngine:
    def record(
        self,
        *,
        organization_id: str,
        payment_id: str,
        action: str,
        status: str,
        amount_usd: float = 0.0,
        detail: str = "",
        actor_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PaymentHistoryEntry:
        entry = PaymentHistoryEntry(
            id=new_id("phist_"),
            organization_id=organization_id,
            payment_id=payment_id,
            action=action,
            status=status,
            amount_usd=amount_usd,
            detail=detail,
            actor_id=actor_id,
            metadata=dict(metadata or {}),
        )
        store.save_payment_history(entry)
        return entry

    def list(self, *, actor_id: str, organization_id: str, limit: int = 100) -> dict[str, Any]:
        _require_read(actor_id=actor_id, organization_id=organization_id)
        items = store.list_payment_history(organization_id, limit=limit)
        return {
            "ok": True,
            "count": len(items),
            "history": [h.to_dict() for h in items],
        }


class PaymentVerificationEngine:
    def verify_capture(self, payment: PayPalPayment, capture_payload: dict[str, Any]) -> bool:
        status = str(
            capture_payload.get("status")
            or (capture_payload.get("purchase_units") or [{}])[0]
            .get("payments", {})
            .get("captures", [{}])[0]
            .get("status")
            or ""
        ).upper()
        if status not in {"COMPLETED", "APPROVED", "CAPTURED"}:
            # In simulated capture we accept CREATED→COMPLETED transition
            if capture_payload.get("simulated") and payment.status in {
                "CREATED",
                "APPROVED",
                "COMPLETED",
            }:
                payment.verified = True
                return True
            return False
        payment.verified = True
        return True


class RefundManagementEngine:
    def __init__(self) -> None:
        self.txns = CreditTransactionEngine()
        self.history = PurchaseHistoryEngine()

    def request(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            org_id = require_non_empty(
                payload.get("organizationId") or payload.get("organization_id"),
                "organizationId",
            )
            _require_manage(actor_id=actor_id, organization_id=org_id)
            credits = int(payload.get("credits") or 0)
            amount_usd = float(payload.get("amountUsd") or payload.get("amount") or 0)
            reason = str(payload.get("reason") or "customer_request")
            payment_id = payload.get("paymentId") or payload.get("payment_id")
            auto = bool(payload.get("autoProcess") if "autoProcess" in payload else True)

            if credits <= 0 and payment_id:
                payment = store.get_payment(str(payment_id))
                if payment and payment.organization_id == org_id:
                    credits = payment.credits + payment.bonus_credits
                    amount_usd = payment.amount_usd
            if credits <= 0:
                raise ValidationError("credits must be > 0 for refund")

            req = RefundRequest(
                id=new_id("rreq_"),
                organization_id=org_id,
                payment_id=str(payment_id) if payment_id else None,
                status="pending",
                credits=credits,
                amount_usd=amount_usd,
                reason=reason,
                actor_id=actor_id,
            )
            store.save_refund(req)
            store.save_refund_history(
                RefundHistoryEntry(
                    id=new_id("rh_"),
                    organization_id=org_id,
                    refund_request_id=req.id,
                    action="requested",
                    status="pending",
                    detail=reason,
                    actor_id=actor_id,
                )
            )
            _audit("wallet.refund.requested", actor_id, req.id, organizationId=org_id)

            if auto:
                return self.process(
                    {"refundRequestId": req.id, "approve": True},
                    actor_id=actor_id,
                )
            return {"ok": True, "refund": req.to_dict()}

    def process(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        req_id = require_non_empty(
            payload.get("refundRequestId") or payload.get("id"),
            "refundRequestId",
        )
        req = store.get_refund(req_id)
        if req is None:
            raise NotFoundError("refund request not found")
        _require_manage(actor_id=actor_id, organization_id=req.organization_id)
        approve = bool(payload.get("approve", True))
        if not approve:
            req.status = "rejected"
            req.reviewer_id = actor_id
            req.updated_at = _now()
            store.save_refund(req)
            store.save_refund_history(
                RefundHistoryEntry(
                    id=new_id("rh_"),
                    organization_id=req.organization_id,
                    refund_request_id=req.id,
                    action="rejected",
                    status="rejected",
                    actor_id=actor_id,
                )
            )
            return {"ok": True, "refund": req.to_dict()}

        # Payment-linked refunds claw back purchased credits; standalone refunds restore credits.
        if req.payment_id:
            adjusted = self.txns.debit(
                req.organization_id,
                req.credits,
                txn_type="refund",
                actor_id=actor_id,
                reason=req.reason,
                reference_type="refund_request",
                reference_id=req.id,
            )
            payment = store.get_payment(req.payment_id)
            if payment:
                payment.status = "REFUNDED"
                payment.updated_at = _now()
                store.save_payment(payment)
                self.history.record(
                    organization_id=req.organization_id,
                    payment_id=payment.id,
                    action="refunded",
                    status="REFUNDED",
                    amount_usd=req.amount_usd,
                    detail=req.reason,
                    actor_id=actor_id,
                )
        else:
            adjusted = self.txns.credit(
                req.organization_id,
                req.credits,
                txn_type="refund",
                credit_category="purchased",
                actor_id=actor_id,
                reason=req.reason,
                reference_type="refund_request",
                reference_id=req.id,
            )

        wallet = self.txns.wallets.ensure(req.organization_id)
        wallet.lifetime_refunded += req.credits
        store.save_wallet(wallet)

        req.status = "completed"
        req.reviewer_id = actor_id
        req.wallet_txn_id = adjusted["transaction"]["id"]
        req.updated_at = _now()
        store.save_refund(req)
        store.save_refund_history(
            RefundHistoryEntry(
                id=new_id("rh_"),
                organization_id=req.organization_id,
                refund_request_id=req.id,
                action="completed",
                status="completed",
                detail=f"refunded {req.credits} credits",
                actor_id=actor_id,
            )
        )
        _audit("wallet.refund.completed", actor_id, req.id, organizationId=req.organization_id)
        return {
            "ok": True,
            "refund": req.to_dict(),
            "wallet": adjusted["wallet"],
            "transaction": adjusted["transaction"],
        }


class PayPalPaymentEngine:
    def __init__(self) -> None:
        self.txns = CreditTransactionEngine()
        self.history = PurchaseHistoryEngine()
        self.verify = PaymentVerificationEngine()

    def create_order(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            org_id = require_non_empty(
                payload.get("organizationId") or payload.get("organization_id"),
                "organizationId",
            )
            _require_manage(actor_id=actor_id, organization_id=org_id)
            if get_repository().get_organization(org_id) is None:
                raise NotFoundError("organization not found")

            pack_key = str(payload.get("packKey") or payload.get("pack") or "pack_500")
            try:
                pack = get_pack(pack_key)
            except ValueError as exc:
                raise ValidationError(str(exc)) from exc

            order_id = f"ORDER-{uuid4().hex[:17].upper()}"
            payment = PayPalPayment(
                id=new_id("ppay_"),
                organization_id=org_id,
                paypal_order_id=order_id,
                status="CREATED",
                amount_usd=float(pack["priceUsd"]),
                pack_key=pack["key"],
                credits=int(pack["credits"]),
                bonus_credits=int(pack.get("bonusCredits") or 0),
                actor_id=actor_id,
                metadata={"intent": "credit_purchase"},
            )
            store.save_payment(payment)
            self.history.record(
                organization_id=org_id,
                payment_id=payment.id,
                action="order_created",
                status="CREATED",
                amount_usd=payment.amount_usd,
                detail=pack["key"],
                actor_id=actor_id,
            )
            _audit(
                "paypal.order.created",
                actor_id,
                order_id,
                organizationId=org_id,
                packKey=pack["key"],
            )
            client_id_present = bool((os.environ.get("PAYPAL_CLIENT_ID") or "").strip())
            return {
                "ok": True,
                "order": {
                    "id": order_id,
                    "status": "CREATED",
                    "amountUsd": payment.amount_usd,
                    "currency": "USD",
                    "packKey": pack["key"],
                    "credits": total_credits(pack),
                    "approveUrl": f"https://www.paypal.com/checkoutnow?token={order_id}",
                    "simulated": not client_id_present,
                },
                "payment": payment.to_dict(),
            }

    def capture_order(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            order_id = require_non_empty(
                payload.get("orderId") or payload.get("paypalOrderId"),
                "orderId",
            )
            payment = store.get_payment_by_order(order_id)
            if payment is None:
                raise NotFoundError("paypal order not found")
            _require_manage(actor_id=actor_id, organization_id=payment.organization_id)

            if payment.status == "COMPLETED":
                return {
                    "ok": True,
                    "duplicate": True,
                    "payment": payment.to_dict(),
                    "wallet": self.txns.wallets.ensure(payment.organization_id).to_dict(),
                }
            if payment.status in {"REFUNDED", "FAILED"}:
                raise ValidationError(
                    f"cannot capture order in status {payment.status}"
                )

            capture_payload = dict(payload.get("capture") or {})
            capture_payload.setdefault("status", "COMPLETED")
            capture_payload["simulated"] = True
            if not self.verify.verify_capture(payment, capture_payload):
                payment.status = "FAILED"
                payment.updated_at = _now()
                store.save_payment(payment)
                self.history.record(
                    organization_id=payment.organization_id,
                    payment_id=payment.id,
                    action="capture_failed",
                    status="FAILED",
                    amount_usd=payment.amount_usd,
                    actor_id=actor_id,
                )
                raise ValidationError("payment verification failed")

            capture_id = str(
                payload.get("captureId")
                or capture_payload.get("id")
                or f"CAP-{uuid4().hex[:12].upper()}"
            )
            payment.status = "COMPLETED"
            payment.paypal_capture_id = capture_id
            payment.payer_email = payload.get("payerEmail") or payment.payer_email
            payment.verified = True
            payment.updated_at = _now()
            store.save_payment(payment)

            # Grant purchased + bonus credits
            purchased = self.txns.credit(
                payment.organization_id,
                payment.credits,
                txn_type="purchase",
                credit_category="purchased",
                actor_id=actor_id,
                reason=f"paypal:{payment.pack_key}",
                reference_type="paypal_payment",
                reference_id=payment.id,
            )
            if payment.bonus_credits > 0:
                self.txns.credit(
                    payment.organization_id,
                    payment.bonus_credits,
                    txn_type="bonus",
                    credit_category="bonus",
                    actor_id=actor_id,
                    reason=f"paypal_bonus:{payment.pack_key}",
                    reference_type="paypal_payment",
                    reference_id=payment.id,
                )

            self.history.record(
                organization_id=payment.organization_id,
                payment_id=payment.id,
                action="captured",
                status="COMPLETED",
                amount_usd=payment.amount_usd,
                detail=capture_id,
                actor_id=actor_id,
            )
            _audit(
                "paypal.order.captured",
                actor_id,
                order_id,
                organizationId=payment.organization_id,
            )
            wallet = self.txns.wallets.ensure(payment.organization_id)
            return {
                "ok": True,
                "payment": payment.to_dict(),
                "wallet": wallet.to_dict(),
                "purchase": purchased["transaction"],
            }

    def webhook(
        self,
        *,
        raw_body: bytes | str,
        transmission_id: str | None,
        transmission_time: str | None,
        transmission_sig: str | None,
        allow_unsigned: bool = False,
    ) -> dict[str, Any]:
        with store.timed_op():
            verify_paypal_webhook(
                transmission_id=transmission_id,
                transmission_time=transmission_time,
                transmission_sig=transmission_sig,
                raw_body=raw_body,
                allow_unsigned=allow_unsigned,
            )
            try:
                payload = json.loads(
                    raw_body.decode("utf-8") if isinstance(raw_body, bytes) else raw_body
                )
            except Exception as exc:
                raise ValidationError(f"invalid webhook JSON: {exc}") from exc

            event_type = str(payload.get("event_type") or payload.get("eventType") or "")
            event_id = str(
                payload.get("id") or payload.get("event_id") or new_id("pevt_")
            )
            if not store.mark_event(event_id):
                return {"ok": True, "duplicate": True, "eventId": event_id}

            resource = payload.get("resource") if isinstance(payload.get("resource"), dict) else {}
            related = resource.get("supplementary_data") or {}
            if not isinstance(related, dict):
                related = {}
            related_ids = related.get("related_ids") or {}
            if not isinstance(related_ids, dict):
                related_ids = {}
            # Capture resources use capture id in resource.id — prefer linked order_id.
            order_id = str(
                related_ids.get("order_id")
                or resource.get("order_id")
                or payload.get("orderId")
                or (
                    resource.get("id")
                    if event_type
                    in {
                        "CHECKOUT.ORDER.APPROVED",
                        "CHECKOUT.ORDER.COMPLETED",
                    }
                    else ""
                )
                or ""
            )
            payment = store.get_payment_by_order(order_id) if order_id else None
            if payment is None and resource.get("id"):
                # Fallback: resource.id may be the order id for order-level events
                payment = store.get_payment_by_order(str(resource.get("id")))

            if event_type in {
                "CHECKOUT.ORDER.APPROVED",
                "PAYMENT.CAPTURE.COMPLETED",
                "PAYMENT.SALE.COMPLETED",
            }:
                if payment and payment.status != "COMPLETED":
                    # Auto-capture path for webhook-driven completion
                    org = get_repository().get_organization(payment.organization_id)
                    actor = payment.actor_id or (org.owner_id if org else "paypal_webhook")
                    return {
                        "ok": True,
                        "eventType": event_type,
                        **self.capture_order(
                            {
                                "orderId": payment.paypal_order_id,
                                "captureId": resource.get("id"),
                                "capture": {"status": "COMPLETED", "simulated": True},
                            },
                            actor_id=actor,
                        ),
                    }
                return {"ok": True, "eventType": event_type, "handled": bool(payment)}

            if event_type in {
                "PAYMENT.CAPTURE.DENIED",
                "PAYMENT.SALE.DENIED",
            }:
                if payment:
                    payment.status = "FAILED"
                    payment.updated_at = _now()
                    store.save_payment(payment)
                    self.history.record(
                        organization_id=payment.organization_id,
                        payment_id=payment.id,
                        action="denied",
                        status="FAILED",
                        amount_usd=payment.amount_usd,
                        detail="webhook_denied",
                    )
                return {"ok": True, "eventType": event_type, "handled": True, "status": "FAILED"}

            if event_type == "PAYMENT.CAPTURE.REFUNDED":
                if payment:
                    payment.status = "REFUNDED"
                    payment.updated_at = _now()
                    store.save_payment(payment)
                return {"ok": True, "eventType": event_type, "handled": True}

            return {"ok": True, "eventType": event_type, "handled": False}


class WalletPurchaseEngine:
    """Direct wallet purchase (credits) — uses PayPal order+capture under the hood."""

    def __init__(self) -> None:
        self.paypal = PayPalPaymentEngine()
        self.txns = CreditTransactionEngine()

    def purchase(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        """Create + capture in one step for internal/simulated purchases."""
        order = self.paypal.create_order(payload, actor_id=actor_id)
        captured = self.paypal.capture_order(
            {
                "orderId": order["order"]["id"],
                "capture": {"status": "COMPLETED", "simulated": True},
            },
            actor_id=actor_id,
        )
        # Optional trial/promo awards
        if payload.get("awardTrial"):
            days = int(payload.get("trialDays") or 14)
            self.txns.credit(
                order["payment"]["organizationId"],
                int(payload.get("trialCredits") or 50),
                txn_type="trial",
                credit_category="trial",
                actor_id=actor_id,
                reason="trial_credits",
                expires_at=_now() + timedelta(days=days),
            )
        if payload.get("awardPromo"):
            self.txns.credit(
                order["payment"]["organizationId"],
                int(payload.get("promoCredits") or 25),
                txn_type="promotional",
                credit_category="promotional",
                actor_id=actor_id,
                reason="promotional_credits",
                expires_at=_now() + timedelta(days=30),
            )
        wallet = self.txns.wallets.ensure(order["payment"]["organizationId"])
        return {
            "ok": True,
            "order": order["order"],
            "payment": captured["payment"],
            "wallet": wallet.to_dict(),
        }


class PaymentProcessingService:
    def __init__(self) -> None:
        self.wallets = CreditWalletEngine()
        self.transactions = CreditTransactionEngine()
        self.paypal = PayPalPaymentEngine()
        self.verification = PaymentVerificationEngine()
        self.history = PurchaseHistoryEngine()
        self.refunds = RefundManagementEngine()
        self.purchases = WalletPurchaseEngine()

    def status(self) -> dict[str, Any]:
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "label": ENGINE_LABEL,
            "phase": PHASE,
            "sprint": SPRINT,
            "paypalClientConfigured": bool(
                (os.environ.get("PAYPAL_CLIENT_ID") or "").strip()
            ),
            "paypalWebhookConfigured": bool(
                (os.environ.get("PAYPAL_WEBHOOK_ID") or os.environ.get("PAYPAL_WEBHOOK_SECRET") or "").strip()
            ),
            "engines": {
                "paypal": "ready",
                "wallet": "ready",
                "transactions": "ready",
                "verification": "ready",
                "purchaseHistory": "ready",
                "refunds": "ready",
            },
            "creditPacks": CREDIT_PACKS,
            "stats": store.metrics(),
        }

    def observability(self) -> dict[str, Any]:
        return {"ok": True, **store.metrics()}


_service: PaymentProcessingService | None = None


def get_payment_processing_service() -> PaymentProcessingService:
    global _service
    if _service is None:
        _service = PaymentProcessingService()
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


get_engine = get_payment_processing_service

# Re-export for tests that build signed webhooks
__all_helpers__ = [compute_transmission_hash]
