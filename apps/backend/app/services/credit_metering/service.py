"""Credit Consumption, Usage Metering & Quota Engine — Phase 8 Sprint 4."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.services.credit_metering import store
from app.services.credit_metering.catalog import (
    FAIR_USAGE_BURST_WINDOW_MINUTES,
    FAIR_USAGE_HARD_MULTIPLIER,
    FAIR_USAGE_SOFT_MULTIPLIER,
    GPU_COST_PER_CREDIT_USD,
    RETAIL_CREDIT_VALUE_USD,
    SERVICE_CREDIT_COSTS,
    credits_for_service,
    normalize_service,
    plan_quota,
    provider_rate,
)
from app.services.credit_metering.models import (
    AIUsageHistoryEntry,
    CostCalculation,
    CreditUsageEvent,
    ProviderCostRate,
    UsageMetricBucket,
    UsageQuota,
    new_id,
)
from app.services.credit_metering.version import (
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


def _require_workspace(
    *, organization_id: str, workspace_id: str | None
) -> None:
    if not workspace_id:
        return
    ForbiddenError, NotFoundError = _auth_errors()
    repo = _repo()
    ws = getattr(repo, "get_workspace", None)
    if callable(ws):
        workspace = ws(workspace_id)
        if workspace is None:
            raise NotFoundError("workspace not found")
        org_attr = getattr(workspace, "organization_id", None) or (
            workspace.get("organizationId") if isinstance(workspace, dict) else None
        )
        if org_attr and org_attr != organization_id:
            raise ForbiddenError("workspace isolation violated")


def _period_keys(now: datetime | None = None) -> dict[str, str]:
    dt = now or _now()
    iso = dt.isocalendar()
    return {
        "day": dt.strftime("%Y-%m-%d"),
        "week": f"{iso.year}-W{iso.week:02d}",
        "month": dt.strftime("%Y-%m"),
    }


def _wallet_balance(organization_id: str) -> int:
    """Best-effort remaining credits from payment wallet then billing."""
    try:
        from app.services.payment_processing.service import get_payment_processing_service

        w = get_payment_processing_service().wallets.ensure(organization_id)
        return int(w.available)
    except Exception:
        pass
    try:
        from app.services.billing.service import get_billing_service

        wallet = get_billing_service().credits.ensure_wallet(organization_id)
        return max(0, int(wallet.balance) - int(getattr(wallet, "reserved", 0) or 0))
    except Exception:
        return 0


def _debit_wallet(
    organization_id: str,
    credits: int,
    *,
    actor_id: str | None,
    reason: str,
    workspace_id: str | None = None,
) -> None:
    try:
        from app.services.payment_processing.service import get_payment_processing_service

        get_payment_processing_service().transactions.debit(
            organization_id,
            credits,
            txn_type="consume",
            actor_id=actor_id,
            reason=reason,
            reference_type="credit_metering",
        )
        return
    except Exception:
        pass
    try:
        from app.services.billing.service import get_billing_service

        get_billing_service().credits.consume(
            organization_id,
            credits,
            actor_id=actor_id,
            reason=reason,
            workspace_id=workspace_id,
        )
    except Exception as exc:
        ValidationError, _ = _validation()
        raise ValidationError(f"credit debit failed: {exc}") from exc


def _org_plan(organization_id: str) -> str:
    try:
        from app.services.billing import store as billing_store

        sub = billing_store.get_org_subscription_by_org(organization_id)
        if sub is not None:
            return str(getattr(sub, "plan_key", None) or "free_trial")
    except Exception:
        pass
    org = _repo().get_organization(organization_id)
    if org is None:
        return "free_trial"
    return str(getattr(org, "plan", None) or "free_trial")


class AICostCalculator:
    def estimate(
        self,
        *,
        organization_id: str,
        service_type: str,
        provider: str = "default",
        quantity: float = 1.0,
        credits: int | None = None,
        persist: bool = True,
    ) -> dict[str, Any]:
        service = normalize_service(service_type)
        credit_amt = credits if credits is not None else credits_for_service(service, quantity)
        rate = provider_rate(provider)
        custom = store.get_provider_cost(provider)
        if custom and custom.active:
            rate = custom.cost_per_credit_usd

        provider_cost = credit_amt * rate
        gpu_cost = credit_amt * GPU_COST_PER_CREDIT_USD
        model_cost = provider_cost  # model ≈ provider for estimate
        retail = credit_amt * RETAIL_CREDIT_VALUE_USD
        operating = provider_cost + gpu_cost
        margin = retail - operating
        margin_pct = (margin / retail * 100.0) if retail > 0 else 0.0

        calc = CostCalculation(
            id=new_id("ccalc_"),
            organization_id=organization_id,
            service_type=service,
            provider=provider,
            credits=credit_amt,
            quantity=quantity,
            provider_cost_usd=provider_cost,
            gpu_cost_usd=gpu_cost,
            model_cost_usd=model_cost,
            retail_value_usd=retail,
            estimated_margin_usd=margin,
            margin_pct=margin_pct,
            metadata={"operatingCostUsd": round(operating, 6)},
        )
        if persist:
            store.save_cost(calc)
            if store.get_provider_cost(provider) is None:
                store.save_provider_cost(
                    ProviderCostRate(
                        id=new_id("pcost_"),
                        provider=provider,
                        cost_per_credit_usd=rate,
                    )
                )
        return {
            "ok": True,
            "estimate": {
                "serviceType": service,
                "provider": provider,
                "credits": credit_amt,
                "quantity": quantity,
                "costPerRequestUsd": round(operating, 6),
                "providerCostUsd": round(provider_cost, 6),
                "gpuCostUsd": round(gpu_cost, 6),
                "aiModelCostUsd": round(model_cost, 6),
                "retailValueUsd": round(retail, 6),
                "estimatedProfitMarginUsd": round(margin, 6),
                "marginPct": round(margin_pct, 2),
                "monthlyOperatingCostUsd": round(operating * 30, 4),
            },
            "calculation": calc.to_dict(),
        }


class QuotaManager:
    def ensure(
        self,
        organization_id: str,
        *,
        workspace_id: str | None = None,
        team_id: str | None = None,
        plan_key: str | None = None,
    ) -> UsageQuota:
        existing = store.get_quota_by_scope(organization_id, workspace_id, team_id)
        if existing:
            return existing
        plan = plan_key or _org_plan(organization_id)
        defaults = plan_quota(plan)
        quota = UsageQuota(
            id=new_id("uquota_"),
            organization_id=organization_id,
            workspace_id=workspace_id,
            team_id=team_id,
            plan_key=plan,
            daily_limit=int(defaults["dailyCredits"]),
            monthly_limit=int(defaults["monthlyCredits"]),
            trial_limit=int(defaults.get("trialCredits") or 0),
            unlimited=bool(defaults.get("unlimited")),
        )
        store.save_quota(quota)
        return quota

    def get(
        self,
        *,
        actor_id: str,
        organization_id: str,
        workspace_id: str | None = None,
        team_id: str | None = None,
    ) -> dict[str, Any]:
        _require_read(actor_id=actor_id, organization_id=organization_id)
        _require_workspace(organization_id=organization_id, workspace_id=workspace_id)
        quota = self.ensure(organization_id, workspace_id=workspace_id, team_id=team_id)
        keys = _period_keys()
        day_used = self._used(organization_id, "day", keys["day"], workspace_id=workspace_id)
        month_used = self._used(
            organization_id, "month", keys["month"], workspace_id=workspace_id
        )
        remaining_daily = (
            None
            if quota.unlimited or quota.daily_limit < 0
            else max(0, quota.daily_limit - day_used)
        )
        remaining_monthly = (
            None
            if quota.unlimited or quota.monthly_limit < 0
            else max(0, quota.monthly_limit - month_used)
        )
        return {
            "ok": True,
            "quota": quota.to_dict(),
            "usage": {
                "dailyUsed": day_used,
                "monthlyUsed": month_used,
                "remainingDaily": remaining_daily,
                "remainingMonthly": remaining_monthly,
                "creditsRemaining": _wallet_balance(organization_id),
            },
        }

    def _used(
        self,
        organization_id: str,
        period: str,
        period_key: str,
        *,
        workspace_id: str | None = None,
    ) -> int:
        bucket = store.find_metric(
            organization_id=organization_id,
            period=period,
            period_key=period_key,
            workspace_id=workspace_id,
            user_id=None,
            provider=None,
        )
        return int(bucket.credits_used) if bucket else 0

    def validate(
        self,
        organization_id: str,
        credits: int,
        *,
        workspace_id: str | None = None,
        team_id: str | None = None,
    ) -> dict[str, Any]:
        quota = self.ensure(organization_id, workspace_id=workspace_id, team_id=team_id)
        if quota.unlimited:
            return {"ok": True, "allowed": True, "reason": "unlimited"}
        keys = _period_keys()
        day_used = self._used(organization_id, "day", keys["day"], workspace_id=workspace_id)
        month_used = self._used(
            organization_id, "month", keys["month"], workspace_id=workspace_id
        )
        ValidationError, _ = _validation()
        if quota.daily_limit >= 0 and day_used + credits > quota.daily_limit:
            raise ValidationError("daily credit quota exceeded")
        if quota.monthly_limit >= 0 and month_used + credits > quota.monthly_limit:
            raise ValidationError("monthly credit quota exceeded")
        if (
            quota.plan_key == "free_trial"
            and quota.trial_limit > 0
            and month_used + credits > quota.trial_limit
        ):
            raise ValidationError("trial credit limit exceeded")
        return {
            "ok": True,
            "allowed": True,
            "dailyUsed": day_used,
            "monthlyUsed": month_used,
        }


class FairUsagePolicyEngine:
    def __init__(self) -> None:
        self.quotas = QuotaManager()

    def evaluate(
        self,
        organization_id: str,
        credits: int,
        *,
        workspace_id: str | None = None,
    ) -> dict[str, Any]:
        quota = self.quotas.ensure(organization_id, workspace_id=workspace_id)
        if quota.unlimited:
            return {"ok": True, "level": "unlimited", "allowed": True}

        keys = _period_keys()
        day_used = self.quotas._used(
            organization_id, "day", keys["day"], workspace_id=workspace_id
        )
        projected = day_used + credits
        daily = quota.daily_limit if quota.daily_limit > 0 else 10**9
        soft = daily * FAIR_USAGE_SOFT_MULTIPLIER
        hard = daily * FAIR_USAGE_HARD_MULTIPLIER

        # Burst: credits in last N minutes
        cutoff = _now() - timedelta(minutes=FAIR_USAGE_BURST_WINDOW_MINUTES)
        recent = [
            e
            for e in store.list_usage(organization_id, workspace_id=workspace_id, limit=500)
            if e.created_at >= cutoff
        ]
        burst = sum(e.credits for e in recent) + credits

        ValidationError, _ = _validation()
        if projected > hard or burst > hard:
            raise ValidationError("fair usage hard limit exceeded")
        level = "normal"
        if projected > soft or burst > soft:
            level = "soft_throttle"
        return {
            "ok": True,
            "allowed": True,
            "level": level,
            "dailyUsed": day_used,
            "burstCredits": burst,
            "softLimit": soft,
            "hardLimit": hard,
        }


class UsageMeteringEngine:
    def bump(
        self,
        *,
        organization_id: str,
        credits: int,
        workspace_id: str | None = None,
        user_id: str | None = None,
        provider: str | None = None,
    ) -> None:
        now = _now()
        keys = _period_keys(now)
        scopes: list[tuple[str | None, str | None, str | None]] = [
            (None, None, None),
        ]
        if workspace_id:
            scopes.append((workspace_id, None, None))
        if user_id:
            scopes.append((None, user_id, None))
        if provider:
            scopes.append((None, None, provider))
        if workspace_id and user_id:
            scopes.append((workspace_id, user_id, None))
        # de-dupe identical scope tuples
        seen: set[tuple[str | None, str | None, str | None]] = set()
        unique_scopes = []
        for scope in scopes:
            if scope not in seen:
                seen.add(scope)
                unique_scopes.append(scope)
        for period, period_key in keys.items():
            for ws, uid, prov in unique_scopes:
                bucket = store.find_metric(
                    organization_id=organization_id,
                    period=period,
                    period_key=period_key,
                    workspace_id=ws,
                    user_id=uid,
                    provider=prov,
                )
                if bucket is None:
                    bucket = UsageMetricBucket(
                        id=new_id("umet_"),
                        organization_id=organization_id,
                        workspace_id=ws,
                        user_id=uid,
                        provider=prov,
                        period=period,
                        period_key=period_key,
                    )
                bucket.credits_used += credits
                bucket.request_count += 1
                bucket.updated_at = now
                store.save_metric(bucket)

    def snapshot(
        self,
        *,
        actor_id: str,
        organization_id: str,
        workspace_id: str | None = None,
    ) -> dict[str, Any]:
        _require_read(actor_id=actor_id, organization_id=organization_id)
        _require_workspace(organization_id=organization_id, workspace_id=workspace_id)
        keys = _period_keys()
        def _sum(period: str, period_key: str) -> int:
            b = store.find_metric(
                organization_id=organization_id,
                period=period,
                period_key=period_key,
                workspace_id=workspace_id,
                user_id=None,
                provider=None,
            )
            return int(b.credits_used) if b else 0

        remaining = _wallet_balance(organization_id)
        day = _sum("day", keys["day"])
        week = _sum("week", keys["week"])
        month = _sum("month", keys["month"])
        return {
            "ok": True,
            "organizationId": organization_id,
            "workspaceId": workspace_id,
            "creditsUsed": {
                "daily": day,
                "weekly": week,
                "monthly": month,
            },
            "creditsRemaining": remaining,
            "periodKeys": keys,
        }


class UsageAnalyticsEngine:
    def analytics(
        self,
        *,
        actor_id: str,
        organization_id: str,
        workspace_id: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        _require_read(actor_id=actor_id, organization_id=organization_id)
        _require_workspace(organization_id=organization_id, workspace_id=workspace_id)
        events = store.list_usage(
            organization_id, workspace_id=workspace_id, limit=limit
        )
        by_service: dict[str, int] = {}
        by_provider: dict[str, int] = {}
        by_user: dict[str, int] = {}
        by_workspace: dict[str, int] = {}
        total = 0
        for e in events:
            total += e.credits
            by_service[e.service_type] = by_service.get(e.service_type, 0) + e.credits
            by_provider[e.provider] = by_provider.get(e.provider, 0) + e.credits
            if e.user_id:
                by_user[e.user_id] = by_user.get(e.user_id, 0) + e.credits
            if e.workspace_id:
                by_workspace[e.workspace_id] = (
                    by_workspace.get(e.workspace_id, 0) + e.credits
                )

        costs = store.list_costs(organization_id, limit=limit)
        op_cost = sum(
            c.provider_cost_usd + c.gpu_cost_usd for c in costs
        )
        margin = sum(c.estimated_margin_usd for c in costs)

        return {
            "ok": True,
            "organizationId": organization_id,
            "workspaceId": workspace_id,
            "totals": {
                "creditsUsed": total,
                "requestCount": len(events),
                "operatingCostUsd": round(op_cost, 4),
                "estimatedMarginUsd": round(margin, 4),
            },
            "byService": by_service,
            "byProvider": by_provider,
            "byUser": by_user,
            "byWorkspace": by_workspace,
            "recent": [e.to_dict() for e in events[:20]],
        }


class CreditConsumptionEngine:
    def __init__(self) -> None:
        self.metering = UsageMeteringEngine()
        self.quotas = QuotaManager()
        self.fair = FairUsagePolicyEngine()
        self.costs = AICostCalculator()

    def consume(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
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

            workspace_id = payload.get("workspaceId") or payload.get("workspace_id")
            team_id = payload.get("teamId") or payload.get("team_id")
            user_id = payload.get("userId") or payload.get("user_id") or actor_id
            _require_workspace(organization_id=org_id, workspace_id=workspace_id)

            service_raw = require_non_empty(
                payload.get("serviceType") or payload.get("service"),
                "serviceType",
            )
            service = normalize_service(str(service_raw))
            quantity = float(payload.get("quantity") or 1.0)
            provider = str(payload.get("provider") or "default").strip().lower()
            credits = int(
                payload.get("credits")
                if payload.get("credits") is not None
                else credits_for_service(service, quantity)
            )
            if credits <= 0:
                raise ValidationError("credits must be > 0")

            # Security: wallet ownership via remaining balance check
            remaining = _wallet_balance(org_id)
            # Seed wallet if empty for managed consume paths that grant first
            if remaining < credits:
                # Try to ensure wallet exists; still reject if insufficient
                try:
                    from app.services.payment_processing.service import (
                        get_payment_processing_service,
                    )

                    get_payment_processing_service().wallets.ensure(org_id)
                    remaining = _wallet_balance(org_id)
                except Exception:
                    pass
            if remaining < credits:
                raise ValidationError("insufficient credits")

            self.quotas.validate(
                org_id, credits, workspace_id=workspace_id, team_id=team_id
            )
            fair = self.fair.evaluate(org_id, credits, workspace_id=workspace_id)

            estimate = self.costs.estimate(
                organization_id=org_id,
                service_type=service,
                provider=provider,
                quantity=quantity,
                credits=credits,
                persist=True,
            )

            _debit_wallet(
                org_id,
                credits,
                actor_id=actor_id,
                reason=f"consume:{service}",
                workspace_id=workspace_id,
            )

            event = CreditUsageEvent(
                id=new_id("cuse_"),
                organization_id=org_id,
                workspace_id=workspace_id,
                user_id=user_id,
                team_id=team_id,
                service_type=service,
                provider=provider,
                credits=credits,
                quantity=quantity,
                resource_type=payload.get("resourceType") or payload.get("resource_type"),
                resource_id=payload.get("resourceId") or payload.get("resource_id"),
                metadata={"fairUsage": fair["level"]},
            )
            store.save_usage(event)
            self.metering.bump(
                organization_id=org_id,
                credits=credits,
                workspace_id=workspace_id,
                user_id=user_id,
                provider=provider,
            )
            hist = AIUsageHistoryEntry(
                id=new_id("aiuh_"),
                organization_id=org_id,
                workspace_id=workspace_id,
                user_id=user_id,
                service_type=service,
                provider=provider,
                credits=credits,
                cost_usd=float(estimate["estimate"]["costPerRequestUsd"]),
                detail=f"consumed {credits} for {service}",
                usage_event_id=event.id,
            )
            store.save_ai_history(hist)
            _audit(
                "credits.consume",
                actor_id,
                event.id,
                organizationId=org_id,
                credits=credits,
                service=service,
            )
            return {
                "ok": True,
                "usage": event.to_dict(),
                "history": hist.to_dict(),
                "creditsRemaining": _wallet_balance(org_id),
                "fairUsage": fair,
                "cost": estimate["estimate"],
            }

    def usage_summary(
        self,
        *,
        actor_id: str,
        organization_id: str,
        workspace_id: str | None = None,
    ) -> dict[str, Any]:
        snap = self.metering.snapshot(
            actor_id=actor_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
        )
        quota = self.quotas.get(
            actor_id=actor_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
        )
        return {**snap, "quota": quota["quota"], "quotaUsage": quota["usage"]}

    def history(
        self,
        *,
        actor_id: str,
        organization_id: str,
        workspace_id: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        _require_read(actor_id=actor_id, organization_id=organization_id)
        _require_workspace(organization_id=organization_id, workspace_id=workspace_id)
        events = store.list_usage(
            organization_id, workspace_id=workspace_id, limit=limit
        )
        history = store.list_ai_history(organization_id, limit=limit)
        return {
            "ok": True,
            "count": len(events),
            "usage": [e.to_dict() for e in events],
            "aiHistory": [h.to_dict() for h in history],
        }


class CreditMeteringService:
    def __init__(self) -> None:
        self.consumption = CreditConsumptionEngine()
        self.metering = UsageMeteringEngine()
        self.costs = AICostCalculator()
        self.quotas = QuotaManager()
        self.fair_usage = FairUsagePolicyEngine()
        self.analytics = UsageAnalyticsEngine()

    def status(self) -> dict[str, Any]:
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "label": ENGINE_LABEL,
            "phase": PHASE,
            "sprint": SPRINT,
            "engines": {
                "consumption": "ready",
                "metering": "ready",
                "costCalculator": "ready",
                "quotaManager": "ready",
                "fairUsage": "ready",
                "analytics": "ready",
            },
            "serviceTypes": list(SERVICE_CREDIT_COSTS.keys()),
            "stats": store.metrics_snapshot(),
        }


_service: CreditMeteringService | None = None


def get_credit_metering_service() -> CreditMeteringService:
    global _service
    if _service is None:
        _service = CreditMeteringService()
    return _service


def reset_engine() -> None:
    global _service
    store.reset_store()
    try:
        from app.services.billing.service import reset_engine as reset_billing
        from app.services.enterprise_auth.engine import reset_engine as reset_ea
        from app.services.multi_tenant.engine import reset_engine as reset_mt
        from app.services.payment_processing.service import (
            reset_engine as reset_pp,
        )

        reset_pp()
        reset_billing()
        reset_mt()
        reset_ea()
    except Exception:
        pass
    _service = None


get_engine = get_credit_metering_service
