"""Enterprise Usage Analytics, Cost Optimization & AI Provider Billing — Phase 8 Sprint 8."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.services.provider_analytics import store
from app.services.provider_analytics.catalog import (
    AI_PROVIDERS,
    BUDGET_ALERT_THRESHOLDS,
    BUDGET_PERIODS,
    BUDGET_SCOPES,
    COST_COMPONENTS,
    CREDIT_RETAIL_VALUE_USD,
    DEFAULT_COMPONENT_COSTS_USD,
    MONTHLY_FIXED_OVERHEAD_USD,
    OPTIMIZATION_MODES,
    provider_profile,
)
from app.services.provider_analytics.models import (
    BudgetEvent,
    BudgetPolicy,
    OptimizationRecord,
    ProfitReport,
    ProviderUsageEvent,
    new_id,
)
from app.services.provider_analytics.version import (
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


class ProviderCostTrackingEngine:
    """Per-provider cost profiles and per-generation cost calculation."""

    def profile(self, provider: str) -> dict[str, Any] | None:
        return store.get_custom_provider(provider) or provider_profile(provider)

    def providers(self) -> dict[str, dict[str, Any]]:
        merged = {k: dict(v) for k, v in AI_PROVIDERS.items()}
        merged.update(store.list_custom_providers())
        return merged

    def register_provider(
        self, name: str, profile: dict[str, Any], *, actor_id: str
    ) -> dict[str, Any]:
        """Register a future provider with its cost/latency/quality profile."""
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            require_non_empty(name, "provider name")
            for field_name in ("costPerRequestUsd", "avgLatencyMs", "qualityScore"):
                if field_name not in profile:
                    raise ValidationError(f"provider profile requires {field_name}")
            record = {
                "label": str(profile.get("label") or name),
                "costPerRequestUsd": float(profile["costPerRequestUsd"]),
                "avgLatencyMs": float(profile["avgLatencyMs"]),
                "qualityScore": float(profile["qualityScore"]),
                "capabilities": [str(c) for c in (profile.get("capabilities") or [])],
            }
            store.save_custom_provider(name, record)
            _audit("provider.registered", actor_id, name)
            return {"ok": True, "provider": name, "profile": record}

    def calculate_cost(
        self,
        provider: str,
        *,
        units: float = 1.0,
        include_rendering: bool = True,
    ) -> dict[str, float]:
        """Full cost breakdown in USD for one generation."""
        ValidationError, _ = _validation()
        profile = self.profile(provider)
        if profile is None:
            raise ValidationError(f"unknown provider: {provider}")
        breakdown = {"provider": profile["costPerRequestUsd"] * units}
        for component, base in DEFAULT_COMPONENT_COSTS_USD.items():
            if component == "rendering" and not include_rendering:
                breakdown[component] = 0.0
            else:
                breakdown[component] = base * units
        breakdown["total"] = round(sum(breakdown.values()), 6)
        return breakdown


class AIUsageAnalyticsEngine:
    """Records provider usage and aggregates analytics across dimensions."""

    def __init__(self, costs: ProviderCostTrackingEngine) -> None:
        self.costs = costs

    def record(
        self,
        organization_id: str,
        provider: str,
        *,
        model: str = "",
        user_id: str | None = None,
        workspace_id: str | None = None,
        status: str = "success",
        latency_ms: float = 0.0,
        credits_charged: float = 0.0,
        units: float = 1.0,
    ) -> ProviderUsageEvent:
        with store.timed_op():
            ValidationError, _ = _validation()
            if status not in ("success", "failed"):
                raise ValidationError(f"unknown usage status: {status}")
            breakdown = self.costs.calculate_cost(provider, units=units)
            total = breakdown.pop("total")
            event = ProviderUsageEvent(
                id=new_id("pue_"),
                organization_id=organization_id,
                provider=provider,
                model=model,
                user_id=user_id,
                workspace_id=workspace_id,
                status=status,
                latency_ms=latency_ms,
                credits_charged=credits_charged,
                cost_breakdown_usd=breakdown,
                total_cost_usd=total,
                revenue_usd=credits_charged * CREDIT_RETAIL_VALUE_USD,
            )
            store.save_usage_event(event)
            return event

    @staticmethod
    def _bucketize(events: list[ProviderUsageEvent], key) -> dict[str, dict[str, Any]]:
        buckets: dict[str, dict[str, Any]] = {}
        for e in events:
            k = key(e)
            if k is None:
                continue
            b = buckets.setdefault(
                str(k),
                {"requests": 0, "successful": 0, "failed": 0, "costUsd": 0.0, "revenueUsd": 0.0},
            )
            b["requests"] += 1
            b["successful" if e.status == "success" else "failed"] += 1
            b["costUsd"] = round(b["costUsd"] + e.total_cost_usd, 6)
            b["revenueUsd"] = round(b["revenueUsd"] + e.revenue_usd, 6)
        return buckets

    def usage(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        with store.timed_op():
            _require_read(actor_id=actor_id, organization_id=organization_id)
            events = store.list_usage_events(organization_id)
            now = _now()
            day_ago = now - timedelta(days=1)
            week_ago = now - timedelta(days=7)
            month_ago = now - timedelta(days=30)
            successful = sum(1 for e in events if e.status == "success")
            return {
                "ok": True,
                "totals": {
                    "requests": len(events),
                    "successful": successful,
                    "failed": len(events) - successful,
                    "successRatePct": round(
                        (successful / len(events) * 100.0) if events else 0.0, 2
                    ),
                },
                "periods": {
                    "daily": sum(1 for e in events if e.created_at >= day_ago),
                    "weekly": sum(1 for e in events if e.created_at >= week_ago),
                    "monthly": sum(1 for e in events if e.created_at >= month_ago),
                },
                "byUser": self._bucketize(events, lambda e: e.user_id),
                "byWorkspace": self._bucketize(events, lambda e: e.workspace_id),
                "byProvider": self._bucketize(events, lambda e: e.provider),
                "byModel": self._bucketize(events, lambda e: e.model or None),
            }

    def provider_analytics(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        with store.timed_op():
            _require_read(actor_id=actor_id, organization_id=organization_id)
            events = store.list_usage_events(organization_id)
            providers = {}
            for name, profile in self.costs.providers().items():
                own = [e for e in events if e.provider == name]
                successful = sum(1 for e in own if e.status == "success")
                latencies = [e.latency_ms for e in own if e.latency_ms > 0]
                providers[name] = {
                    "label": profile["label"],
                    "requests": len(own),
                    "successful": successful,
                    "failed": len(own) - successful,
                    "costUsd": round(sum(e.total_cost_usd for e in own), 6),
                    "revenueUsd": round(sum(e.revenue_usd for e in own), 6),
                    "avgLatencyMs": round(
                        sum(latencies) / len(latencies) if latencies else 0.0, 3
                    ),
                    "profile": profile,
                }
            return {"ok": True, "providers": providers}


class InternalBillingEngine:
    """Aggregates internal cost/revenue totals for the organization."""

    def costs(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        with store.timed_op():
            _require_read(actor_id=actor_id, organization_id=organization_id)
            events = store.list_usage_events(organization_id)
            month_ago = _now() - timedelta(days=30)
            components = {c: 0.0 for c in COST_COMPONENTS}
            monthly_cost = 0.0
            for e in events:
                for component, value in e.cost_breakdown_usd.items():
                    components[component] = round(components.get(component, 0.0) + value, 6)
                if e.created_at >= month_ago:
                    monthly_cost += e.total_cost_usd
            total = round(sum(components.values()), 6)
            count = len(events)
            return {
                "ok": True,
                "components": components,
                "totalCostUsd": total,
                "costPerGenerationUsd": round(total / count, 6) if count else 0.0,
                "monthlyOperatingCostUsd": round(
                    monthly_cost + MONTHLY_FIXED_OVERHEAD_USD, 6
                ),
                "fixedOverheadUsd": MONTHLY_FIXED_OVERHEAD_USD,
                "generations": count,
            }

    def revenue(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        with store.timed_op():
            _require_read(actor_id=actor_id, organization_id=organization_id)
            events = store.list_usage_events(organization_id)
            month_ago = _now() - timedelta(days=30)
            total = round(sum(e.revenue_usd for e in events), 6)
            monthly = round(
                sum(e.revenue_usd for e in events if e.created_at >= month_ago), 6
            )
            credits = round(sum(e.credits_charged for e in events), 4)
            return {
                "ok": True,
                "revenueUsd": total,
                "monthlyRevenueUsd": monthly,
                "creditsBilled": credits,
                "creditRetailValueUsd": CREDIT_RETAIL_VALUE_USD,
            }


class BudgetControlEngine:
    """Budget policies, spending limits, and threshold alerts."""

    def _policy(self, organization_id: str, scope: str, scope_id: str) -> BudgetPolicy:
        policy = store.get_budget_policy(scope, scope_id)
        if policy is None:
            policy = BudgetPolicy(
                id=new_id("bud_"),
                organization_id=organization_id,
                scope=scope,
                scope_id=scope_id,
            )
            store.save_budget_policy(policy)
        return policy

    def get(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        with store.timed_op():
            _require_read(actor_id=actor_id, organization_id=organization_id)
            policy = self._policy(organization_id, "organization", organization_id)
            workspaces = [
                p.to_dict()
                for p in store.list_budget_policies(organization_id)
                if p.scope == "workspace"
            ]
            spent = self._spent(organization_id, "organization", organization_id)
            events = store.list_budget_events(organization_id, limit=50)
            return {
                "ok": True,
                "budget": policy.to_dict(),
                "spending": spent,
                "workspaceBudgets": workspaces,
                "recentEvents": [e.to_dict() for e in events],
            }

    def update(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = require_non_empty(
                payload.get("organizationId") or payload.get("organization_id"),
                "organizationId",
            )
            _require_manage(actor_id=actor_id, organization_id=org_id)
            scope = str(payload.get("scope") or "organization")
            if scope not in BUDGET_SCOPES:
                raise ValidationError(f"unknown budget scope: {scope}")
            scope_id = str(payload.get("scopeId") or org_id)
            if scope == "workspace" and scope_id == org_id:
                raise ValidationError("workspace budgets require scopeId")
            daily = float(payload.get("dailyLimitUsd") or 0.0)
            monthly = float(payload.get("monthlyLimitUsd") or 0.0)
            if daily < 0 or monthly < 0:
                raise ValidationError("budget limits must be >= 0")
            policy = self._policy(org_id, scope, scope_id)
            policy.daily_limit_usd = daily
            policy.monthly_limit_usd = monthly
            if "alertsEnabled" in payload:
                policy.alerts_enabled = bool(payload["alertsEnabled"])
            if "hardStop" in payload:
                policy.hard_stop = bool(payload["hardStop"])
            policy.updated_by = actor_id
            policy.updated_at = _now()
            store.save_budget_policy(policy)
            store.save_budget_event(
                BudgetEvent(
                    id=new_id("bev_"),
                    organization_id=org_id,
                    policy_id=policy.id,
                    event_type="budget_updated",
                    detail=f"daily={daily} monthly={monthly} scope={scope}",
                )
            )
            _audit(
                "budget.updated",
                actor_id,
                f"{scope}:{scope_id}",
                organizationId=org_id,
                dailyLimitUsd=daily,
                monthlyLimitUsd=monthly,
            )
            return {"ok": True, "budget": policy.to_dict()}

    def _spent(self, organization_id: str, scope: str, scope_id: str) -> dict[str, float]:
        events = store.list_usage_events(
            organization_id,
            workspace_id=scope_id if scope == "workspace" else None,
        )
        now = _now()
        day_ago = now - timedelta(days=1)
        month_ago = now - timedelta(days=30)
        return {
            "dailySpentUsd": round(
                sum(e.total_cost_usd for e in events if e.created_at >= day_ago), 6
            ),
            "monthlySpentUsd": round(
                sum(e.total_cost_usd for e in events if e.created_at >= month_ago), 6
            ),
        }

    def check_spend(
        self,
        organization_id: str,
        *,
        additional_cost_usd: float = 0.0,
        workspace_id: str | None = None,
    ) -> dict[str, Any]:
        """Evaluate budget before spending; emits alerts and enforces hard stops."""
        with store.timed_op():
            scope = "workspace" if workspace_id else "organization"
            scope_id = workspace_id or organization_id
            policy = self._policy(organization_id, scope, scope_id)
            spent = self._spent(organization_id, scope, scope_id)
            allowed = True
            reason = ""
            alerts: list[dict[str, Any]] = []
            for period, limit, current in (
                ("daily", policy.daily_limit_usd, spent["dailySpentUsd"]),
                ("monthly", policy.monthly_limit_usd, spent["monthlySpentUsd"]),
            ):
                if limit <= 0:
                    continue
                projected = current + additional_cost_usd
                if policy.alerts_enabled:
                    for threshold in BUDGET_ALERT_THRESHOLDS:
                        if current < limit * threshold <= projected:
                            event = BudgetEvent(
                                id=new_id("bev_"),
                                organization_id=organization_id,
                                policy_id=policy.id,
                                event_type="threshold_alert",
                                period=period,
                                threshold_pct=threshold * 100,
                                spent_usd=projected,
                                limit_usd=limit,
                                detail=f"{period} budget {int(threshold * 100)}% reached",
                            )
                            store.save_budget_event(event)
                            alerts.append(event.to_dict())
                if projected > limit:
                    event = BudgetEvent(
                        id=new_id("bev_"),
                        organization_id=organization_id,
                        policy_id=policy.id,
                        event_type="limit_reached",
                        period=period,
                        threshold_pct=100.0,
                        spent_usd=projected,
                        limit_usd=limit,
                        detail=f"{period} budget limit exceeded",
                    )
                    store.save_budget_event(event)
                    alerts.append(event.to_dict())
                    if policy.hard_stop:
                        allowed = False
                        reason = f"{period} spending limit reached"
            return {
                "ok": True,
                "allowed": allowed,
                "reason": reason,
                "alerts": alerts,
                "spending": spent,
                "budget": policy.to_dict(),
            }


class CostOptimizationEngine:
    """Recommends providers by cost, speed, quality, and failover order."""

    def __init__(self, costs: ProviderCostTrackingEngine) -> None:
        self.costs = costs

    def _candidates(self, capability: str | None) -> list[tuple[str, dict[str, Any]]]:
        return [
            (name, profile)
            for name, profile in self.costs.providers().items()
            if capability is None or capability in profile.get("capabilities", [])
        ]

    def recommendations(
        self,
        *,
        actor_id: str,
        organization_id: str,
        mode: str = "balanced",
        capability: str | None = None,
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            _require_read(actor_id=actor_id, organization_id=organization_id)
            if mode not in OPTIMIZATION_MODES:
                raise ValidationError(f"unknown optimization mode: {mode}")
            candidates = self._candidates(capability)
            if not candidates:
                raise ValidationError(
                    f"no providers support capability: {capability}"
                )

            def score(profile: dict[str, Any]) -> float:
                cost = profile["costPerRequestUsd"]
                latency = profile["avgLatencyMs"]
                quality = profile["qualityScore"]
                if mode == "lowest_cost":
                    return -cost
                if mode == "fastest":
                    return -latency
                if mode == "best_quality":
                    return quality
                # balanced: normalize each dimension and weight equally
                return quality / 10.0 - cost / 0.05 * 0.5 - latency / 3000.0 * 0.5

            ranked = sorted(candidates, key=lambda c: score(c[1]), reverse=True)
            ranking = [
                {
                    "provider": name,
                    "label": profile["label"],
                    "costPerRequestUsd": profile["costPerRequestUsd"],
                    "avgLatencyMs": profile["avgLatencyMs"],
                    "qualityScore": profile["qualityScore"],
                }
                for name, profile in ranked
            ]
            best_name, best = ranked[0]
            most_expensive = max(c[1]["costPerRequestUsd"] for c in candidates)
            savings = round(most_expensive - best["costPerRequestUsd"], 6)
            record = OptimizationRecord(
                id=new_id("opt_"),
                organization_id=organization_id,
                mode=mode,
                capability=capability or "",
                selected_provider=best_name,
                estimated_cost_usd=best["costPerRequestUsd"],
                estimated_latency_ms=best["avgLatencyMs"],
                quality_score=best["qualityScore"],
                savings_usd=savings if mode == "lowest_cost" else 0.0,
                reason=f"selected by {mode} policy",
                ranking=ranking,
            )
            store.save_optimization(record)
            return {
                "ok": True,
                "mode": mode,
                "capability": capability,
                "recommended": ranking[0],
                "failoverOrder": [r["provider"] for r in ranking],
                "ranking": ranking,
                "costSavingOpportunities": self._saving_opportunities(organization_id),
                "recommendationId": record.id,
            }

    def _saving_opportunities(self, organization_id: str) -> list[dict[str, Any]]:
        events = store.list_usage_events(organization_id)
        by_provider: dict[str, float] = {}
        for e in events:
            by_provider[e.provider] = by_provider.get(e.provider, 0.0) + e.total_cost_usd
        providers = self.costs.providers()
        if not providers:
            return []
        cheapest = min(providers.items(), key=lambda p: p[1]["costPerRequestUsd"])
        opportunities = []
        for name, spent in by_provider.items():
            profile = providers.get(name)
            if profile is None or name == cheapest[0]:
                continue
            unit_diff = profile["costPerRequestUsd"] - cheapest[1]["costPerRequestUsd"]
            if unit_diff <= 0:
                continue
            requests = sum(1 for e in events if e.provider == name)
            opportunities.append(
                {
                    "fromProvider": name,
                    "toProvider": cheapest[0],
                    "requests": requests,
                    "potentialSavingsUsd": round(unit_diff * requests, 6),
                }
            )
        opportunities.sort(key=lambda o: o["potentialSavingsUsd"], reverse=True)
        return opportunities

    def history(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        with store.timed_op():
            _require_read(actor_id=actor_id, organization_id=organization_id)
            items = store.list_optimizations(organization_id)
            return {"ok": True, "count": len(items), "history": [o.to_dict() for o in items]}


class ProfitAnalyticsEngine:
    """Revenue vs cost analytics and monthly profit reports."""

    def profit(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        with store.timed_op():
            _require_read(actor_id=actor_id, organization_id=organization_id)
            events = store.list_usage_events(organization_id)
            revenue = sum(e.revenue_usd for e in events)
            provider_cost = sum(
                e.cost_breakdown_usd.get("provider", 0.0) for e in events
            )
            infra_cost = sum(
                v
                for e in events
                for k, v in e.cost_breakdown_usd.items()
                if k != "provider"
            )
            gross = revenue - provider_cost
            net = gross - infra_cost - MONTHLY_FIXED_OVERHEAD_USD
            report = ProfitReport(
                id=new_id("pft_"),
                organization_id=organization_id,
                period=_now().strftime("%Y-%m"),
                revenue_usd=revenue,
                provider_cost_usd=provider_cost,
                infrastructure_cost_usd=infra_cost,
                fixed_overhead_usd=MONTHLY_FIXED_OVERHEAD_USD,
                gross_profit_usd=gross,
                net_profit_usd=net,
                margin_pct=(gross / revenue * 100.0) if revenue else 0.0,
                generated_by=actor_id,
            )
            store.save_profit_report(report)
            return {
                "ok": True,
                "profit": report.to_dict(),
                "reports": [r.to_dict() for r in store.list_profit_reports(organization_id, limit=12)],
            }


class ProviderAnalyticsService:
    def __init__(self) -> None:
        self.costs = ProviderCostTrackingEngine()
        self.analytics = AIUsageAnalyticsEngine(self.costs)
        self.billing = InternalBillingEngine()
        self.budgets = BudgetControlEngine()
        self.optimizer = CostOptimizationEngine(self.costs)
        self.profit = ProfitAnalyticsEngine()

    def status(self) -> dict[str, Any]:
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "label": ENGINE_LABEL,
            "phase": PHASE,
            "sprint": SPRINT,
            "engines": {
                "usageAnalytics": "ready",
                "providerCostTracking": "ready",
                "internalBilling": "ready",
                "costOptimization": "ready",
                "budgetControl": "ready",
                "profitAnalytics": "ready",
            },
            "providers": sorted(self.costs.providers().keys()),
            "budgetPeriods": list(BUDGET_PERIODS),
            "optimizationModes": list(OPTIMIZATION_MODES),
            "stats": store.metrics(),
        }


_service: ProviderAnalyticsService | None = None


def get_provider_analytics_service() -> ProviderAnalyticsService:
    global _service
    if _service is None:
        _service = ProviderAnalyticsService()
    return _service


def reset_engine() -> None:
    global _service
    store.reset_store()
    _service = None


get_engine = get_provider_analytics_service
