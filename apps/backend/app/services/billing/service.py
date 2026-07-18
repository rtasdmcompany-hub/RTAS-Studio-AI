"""Enterprise Billing & Subscription Foundation — Phase 8 Sprint 1."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.services.billing import store
from app.services.billing.catalog import (
    DEFAULT_PLANS,
    normalize_cycle,
    normalize_plan_key,
)
from app.services.billing.models import (
    BillingProfile,
    CreditTransaction,
    CreditWallet,
    Invoice,
    OrganizationSubscription,
    SubscriptionPlan,
    UsageRecord,
    UserSubscription,
    new_id,
)
from app.services.billing.version import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    PHASE,
    SPRINT,
)
from app.services.enterprise_auth.audit import log_auth_event
from app.services.enterprise_auth.errors import ForbiddenError, NotFoundError
from app.services.enterprise_auth.middleware import require_access
from app.services.multi_tenant.repository import get_repository
from app.services.multi_tenant.validation import ValidationError, require_non_empty


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


def _require_billing_read(
    *,
    actor_id: str,
    organization_id: str,
    workspace_id: str | None = None,
) -> None:
    require_access(
        user_id=actor_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        permission="org.read",
    )
    if workspace_id:
        ws = get_repository().get_workspace(workspace_id)
        if ws is None or ws.organization_id != organization_id:
            raise ForbiddenError("workspace isolation violation")


def _require_billing_manage(
    *,
    actor_id: str,
    organization_id: str,
) -> None:
    require_access(
        user_id=actor_id,
        organization_id=organization_id,
        permission="org.update",
    )
    member = get_repository().get_member_by_org_user(organization_id, actor_id)
    if member is None:
        raise ForbiddenError("subscription ownership denied")
    if member.role_key not in {"owner", "admin", "manager"}:
        raise ForbiddenError("subscription ownership denied")


def _period_end(cycle: str, start: datetime) -> datetime:
    if cycle == "yearly":
        return start + timedelta(days=365)
    return start + timedelta(days=30)


class PlanManagementEngine:
    def ensure_defaults(self) -> None:
        if store.is_seeded():
            return
        for raw in DEFAULT_PLANS:
            existing = store.get_plan_by_key(raw["key"])
            if existing:
                continue
            plan = SubscriptionPlan(
                id=new_id("plan_"),
                key=raw["key"],
                name=raw["name"],
                description=raw.get("description") or "",
                monthly_price_usd=float(raw["monthlyPriceUsd"]),
                yearly_price_usd=float(raw["yearlyPriceUsd"]),
                credits_monthly=int(raw["creditsMonthly"]),
                credits_yearly=int(raw["creditsYearly"]),
                max_workspaces=int(raw["maxWorkspaces"]),
                max_teams=int(raw["maxTeams"]),
                max_members=int(raw["maxMembers"]),
                max_projects=int(raw["maxProjects"]),
                ai_provider_limit=int(raw["aiProviderLimit"]),
                features=list(raw.get("features") or []),
                is_public=bool(raw.get("isPublic", True)),
                trial_days=int(raw.get("trialDays") or 0),
            )
            store.save_plan(plan)
        store.mark_seeded()

    def list_plans(self) -> dict[str, Any]:
        self.ensure_defaults()
        plans = store.list_plans(public_only=True)
        return {
            "ok": True,
            "count": len(plans),
            "plans": [p.to_dict() for p in plans],
            "billingCycles": ["monthly", "yearly"],
        }

    def get_plan(self, plan_key: str) -> SubscriptionPlan:
        self.ensure_defaults()
        key = normalize_plan_key(plan_key)
        plan = store.get_plan_by_key(key)
        if plan is None:
            raise NotFoundError("plan not found")
        return plan


class CreditEngine:
    def ensure_wallet(self, organization_id: str) -> CreditWallet:
        wallet = store.get_wallet_by_org(organization_id)
        if wallet:
            return wallet
        wallet = CreditWallet(
            id=new_id("wal_"),
            organization_id=organization_id,
            balance=0,
        )
        store.save_wallet(wallet)
        return wallet

    def grant(
        self,
        organization_id: str,
        amount: int,
        *,
        actor_id: str | None = None,
        reason: str = "grant",
        reference_type: str | None = None,
        reference_id: str | None = None,
    ) -> dict[str, Any]:
        if amount <= 0:
            raise ValidationError("credit amount must be > 0")
        wallet = self.ensure_wallet(organization_id)
        wallet.balance += amount
        wallet.lifetime_granted += amount
        wallet.updated_at = _now()
        store.save_wallet(wallet)
        txn = CreditTransaction(
            id=new_id("ctx_"),
            wallet_id=wallet.id,
            organization_id=organization_id,
            amount=amount,
            balance_after=wallet.balance,
            txn_type="credit",
            reason=reason,
            actor_id=actor_id,
            reference_type=reference_type,
            reference_id=reference_id,
        )
        store.save_credit_txn(txn)
        if actor_id:
            _audit(
                "billing.credits.granted",
                actor_id,
                reason,
                organizationId=organization_id,
                amount=amount,
            )
        return {"ok": True, "wallet": wallet.to_dict(), "transaction": txn.to_dict()}

    def consume(
        self,
        organization_id: str,
        amount: int,
        *,
        actor_id: str | None = None,
        reason: str = "usage",
        workspace_id: str | None = None,
    ) -> dict[str, Any]:
        if amount <= 0:
            raise ValidationError("credit amount must be > 0")
        wallet = self.ensure_wallet(organization_id)
        available = wallet.balance - wallet.reserved
        if available < amount:
            raise ValidationError("insufficient credits")
        wallet.balance -= amount
        wallet.lifetime_spent += amount
        wallet.updated_at = _now()
        store.save_wallet(wallet)
        txn = CreditTransaction(
            id=new_id("ctx_"),
            wallet_id=wallet.id,
            organization_id=organization_id,
            amount=-amount,
            balance_after=wallet.balance,
            txn_type="debit",
            reason=reason,
            actor_id=actor_id,
            workspace_id=workspace_id,
        )
        store.save_credit_txn(txn)
        return {"ok": True, "wallet": wallet.to_dict(), "transaction": txn.to_dict()}

    def get(
        self,
        organization_id: str,
        *,
        actor_id: str,
        workspace_id: str | None = None,
    ) -> dict[str, Any]:
        _require_billing_read(
            actor_id=actor_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
        )
        wallet = self.ensure_wallet(organization_id)
        txns = store.list_credit_txns(organization_id, limit=25)
        return {
            "ok": True,
            "wallet": wallet.to_dict(),
            "transactions": [t.to_dict() for t in txns],
            "count": len(txns),
        }


class UsageTrackingEngine:
    def record(self, payload: dict[str, Any], *, actor_id: str | None = None) -> dict[str, Any]:
        org_id = require_non_empty(
            payload.get("organizationId") or payload.get("organization_id"),
            "organizationId",
        )
        usage_type = require_non_empty(
            payload.get("usageType") or payload.get("type") or "ai_generation",
            "usageType",
            max_len=80,
        )
        quantity = float(payload.get("quantity") or 1)
        credits = int(payload.get("creditsConsumed") or payload.get("credits") or 0)
        workspace_id = payload.get("workspaceId") or payload.get("workspace_id")
        rec = UsageRecord(
            id=new_id("use_"),
            organization_id=org_id,
            workspace_id=str(workspace_id) if workspace_id else None,
            user_id=actor_id or payload.get("userId"),
            usage_type=usage_type,
            quantity=quantity,
            credits_consumed=credits,
            provider=payload.get("provider"),
            resource_type=payload.get("resourceType"),
            resource_id=payload.get("resourceId"),
            metadata=dict(payload.get("metadata") or {}),
        )
        store.save_usage(rec)
        if credits > 0:
            CreditEngine().consume(
                org_id,
                credits,
                actor_id=actor_id,
                reason=f"usage:{usage_type}",
                workspace_id=str(workspace_id) if workspace_id else None,
            )
        if actor_id:
            _audit("billing.usage.recorded", actor_id, usage_type, organizationId=org_id)
        return {"ok": True, "usage": rec.to_dict()}

    def list(
        self,
        *,
        actor_id: str,
        organization_id: str,
        workspace_id: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        _require_billing_read(
            actor_id=actor_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
        )
        items = store.list_usage(
            organization_id, workspace_id=workspace_id, limit=limit
        )
        total_credits = sum(i.credits_consumed for i in items)
        by_type: dict[str, float] = {}
        for i in items:
            by_type[i.usage_type] = by_type.get(i.usage_type, 0) + i.quantity
        return {
            "ok": True,
            "organizationId": organization_id,
            "workspaceId": workspace_id,
            "count": len(items),
            "totalCreditsConsumed": total_credits,
            "byType": by_type,
            "records": [i.to_dict() for i in items],
        }


class InvoiceEngine:
    def create_for_subscription(
        self,
        sub: OrganizationSubscription,
        plan: SubscriptionPlan,
        *,
        actor_id: str | None = None,
    ) -> Invoice:
        price = (
            plan.yearly_price_usd
            if sub.billing_cycle == "yearly"
            else plan.monthly_price_usd
        )
        now = _now()
        inv = Invoice(
            id=new_id("inv_"),
            organization_id=sub.organization_id,
            subscription_id=sub.id,
            invoice_number=f"INV-{now.strftime('%Y%m%d')}-{new_id('')[:8].upper()}",
            status="open" if price > 0 else "paid",
            subtotal_usd=price,
            tax_usd=0.0,
            total_usd=price,
            billing_cycle=sub.billing_cycle,
            plan_key=plan.key,
            period_start=sub.current_period_start,
            period_end=sub.current_period_end,
            issued_at=now,
            due_at=now + timedelta(days=14),
            paid_at=now if price == 0 else None,
            line_items=[
                {
                    "description": f"{plan.name} ({sub.billing_cycle})",
                    "amountUsd": price,
                    "quantity": 1,
                }
            ],
        )
        store.save_invoice(inv)
        if actor_id:
            _audit(
                "billing.invoice.created",
                actor_id,
                inv.invoice_number,
                organizationId=sub.organization_id,
            )
        return inv

    def list(
        self, *, actor_id: str, organization_id: str, limit: int = 50
    ) -> dict[str, Any]:
        _require_billing_read(actor_id=actor_id, organization_id=organization_id)
        items = store.list_invoices(organization_id, limit=limit)
        return {
            "ok": True,
            "count": len(items),
            "invoices": [i.to_dict() for i in items],
        }


class SubscriptionEngine:
    def __init__(self) -> None:
        self.plans = PlanManagementEngine()
        self.credits = CreditEngine()
        self.invoices = InvoiceEngine()

    def get(
        self,
        *,
        actor_id: str,
        organization_id: str,
    ) -> dict[str, Any]:
        _require_billing_read(actor_id=actor_id, organization_id=organization_id)
        self.plans.ensure_defaults()
        sub = store.get_org_subscription_by_org(organization_id)
        plan = store.get_plan_by_key(sub.plan_key) if sub else None
        wallet = self.credits.ensure_wallet(organization_id)
        return {
            "ok": True,
            "organizationId": organization_id,
            "subscription": sub.to_dict() if sub else None,
            "plan": plan.to_dict() if plan else None,
            "credits": wallet.to_dict(),
            "hasSubscription": sub is not None,
        }

    def create(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            org_id = require_non_empty(
                payload.get("organizationId") or payload.get("organization_id"),
                "organizationId",
            )
            _require_billing_manage(actor_id=actor_id, organization_id=org_id)
            if get_repository().get_organization(org_id) is None:
                raise NotFoundError("organization not found")
            if store.get_org_subscription_by_org(org_id):
                raise ValidationError("organization already has a subscription")

            plan_key = normalize_plan_key(
                str(payload.get("planKey") or payload.get("plan") or "free_trial")
            )
            cycle = normalize_cycle(
                str(payload.get("billingCycle") or payload.get("cycle") or "monthly")
            )
            plan = self.plans.get_plan(plan_key)
            start = _now()
            status = "trialing" if plan_key == "free_trial" else "active"
            end = (
                start + timedelta(days=plan.trial_days or 14)
                if status == "trialing"
                else _period_end(cycle, start)
            )
            seats = int(payload.get("seats") or 1)
            sub = OrganizationSubscription(
                id=new_id("osub_"),
                organization_id=org_id,
                plan_key=plan_key,
                billing_cycle=cycle,
                status=status,
                owner_user_id=actor_id,
                seats=max(1, seats),
                current_period_start=start,
                current_period_end=end,
                metadata=dict(payload.get("metadata") or {}),
            )
            store.save_org_subscription(sub)

            # Mirror user subscription for the owner
            user_sub = UserSubscription(
                id=new_id("usub_"),
                user_id=actor_id,
                plan_key=plan_key,
                billing_cycle=cycle,
                status=status,
                organization_id=org_id,
                current_period_start=start,
                current_period_end=end,
            )
            store.save_user_subscription(user_sub)

            credit_amount = (
                plan.credits_yearly if cycle == "yearly" else plan.credits_monthly
            )
            if status == "trialing":
                credit_amount = plan.credits_monthly
            grant = self.credits.grant(
                org_id,
                credit_amount,
                actor_id=actor_id,
                reason=f"subscription:{plan_key}:{cycle}",
                reference_type="subscription",
                reference_id=sub.id,
            )
            invoice = self.invoices.create_for_subscription(
                sub, plan, actor_id=actor_id
            )
            profile = store.get_profile_by_org(org_id)
            if profile is None:
                profile = BillingProfile(
                    id=new_id("bprof_"),
                    organization_id=org_id,
                    company_name=str(payload.get("companyName") or ""),
                    billing_email=str(payload.get("billingEmail") or ""),
                )
                store.save_profile(profile)

            _audit(
                "billing.subscription.created",
                actor_id,
                plan_key,
                organizationId=org_id,
                cycle=cycle,
            )
            return {
                "ok": True,
                "subscription": sub.to_dict(),
                "userSubscription": user_sub.to_dict(),
                "plan": plan.to_dict(),
                "credits": grant["wallet"],
                "invoice": invoice.to_dict(),
                "billingProfile": profile.to_dict(),
            }

    def update(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            org_id = require_non_empty(
                payload.get("organizationId") or payload.get("organization_id"),
                "organizationId",
            )
            _require_billing_manage(actor_id=actor_id, organization_id=org_id)
            sub = store.get_org_subscription_by_org(org_id)
            if sub is None:
                raise NotFoundError("subscription not found")

            changed_plan = False
            if payload.get("planKey") or payload.get("plan"):
                new_key = normalize_plan_key(
                    str(payload.get("planKey") or payload.get("plan"))
                )
                if new_key != sub.plan_key:
                    sub.plan_key = new_key
                    changed_plan = True
                    if new_key == "free_trial":
                        sub.status = "trialing"
                    elif sub.status in {"expired", "canceled"}:
                        sub.status = "active"

            if payload.get("billingCycle") or payload.get("cycle"):
                sub.billing_cycle = normalize_cycle(
                    str(payload.get("billingCycle") or payload.get("cycle"))
                )

            if payload.get("status"):
                status = str(payload["status"]).strip().lower()
                if status not in {
                    "trialing",
                    "active",
                    "past_due",
                    "canceled",
                    "expired",
                    "paused",
                }:
                    raise ValidationError("invalid subscription status")
                sub.status = status

            if "cancelAtPeriodEnd" in payload or "cancel_at_period_end" in payload:
                sub.cancel_at_period_end = bool(
                    payload.get("cancelAtPeriodEnd")
                    if "cancelAtPeriodEnd" in payload
                    else payload.get("cancel_at_period_end")
                )

            if payload.get("seats") is not None:
                sub.seats = max(1, int(payload["seats"]))

            sub.updated_at = _now()
            store.save_org_subscription(sub)
            plan = self.plans.get_plan(sub.plan_key)

            invoice = None
            if changed_plan:
                credit_amount = (
                    plan.credits_yearly
                    if sub.billing_cycle == "yearly"
                    else plan.credits_monthly
                )
                self.credits.grant(
                    org_id,
                    credit_amount,
                    actor_id=actor_id,
                    reason=f"plan_change:{sub.plan_key}",
                    reference_type="subscription",
                    reference_id=sub.id,
                )
                invoice = self.invoices.create_for_subscription(
                    sub, plan, actor_id=actor_id
                )

            _audit(
                "billing.subscription.updated",
                actor_id,
                sub.plan_key,
                organizationId=org_id,
            )
            return {
                "ok": True,
                "subscription": sub.to_dict(),
                "plan": plan.to_dict(),
                "invoice": invoice.to_dict() if invoice else None,
            }


class BillingEngine:
    """Top-level billing facade."""

    def status(self) -> dict[str, Any]:
        PlanManagementEngine().ensure_defaults()
        m = store.metrics()
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "label": ENGINE_LABEL,
            "phase": PHASE,
            "sprint": SPRINT,
            "engines": {
                "billing": "ready",
                "subscription": "ready",
                "plans": "ready",
                "credits": "ready",
                "usage": "ready",
                "invoices": "ready",
            },
            "stats": m,
        }

    def observability(self) -> dict[str, Any]:
        return {"ok": True, **store.metrics()}


class BillingService:
    def __init__(self) -> None:
        self.billing = BillingEngine()
        self.plans = PlanManagementEngine()
        self.subscriptions = SubscriptionEngine()
        self.credits = CreditEngine()
        self.usage = UsageTrackingEngine()
        self.invoices = InvoiceEngine()

    def status(self) -> dict[str, Any]:
        return self.billing.status()

    def observability(self) -> dict[str, Any]:
        return self.billing.observability()


_service: BillingService | None = None


def get_billing_service() -> BillingService:
    global _service
    if _service is None:
        _service = BillingService()
        _service.plans.ensure_defaults()
    return _service


def reset_engine() -> None:
    global _service
    store.reset_store()
    try:
        from app.services.multi_tenant.engine import reset_engine as reset_mt
        from app.services.enterprise_auth.engine import reset_engine as reset_ea

        reset_mt()
        reset_ea()
    except Exception:
        pass
    _service = None


get_engine = get_billing_service
