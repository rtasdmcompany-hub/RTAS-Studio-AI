"""AI Model Routing Engine — plan, select, failover, analytics."""

from __future__ import annotations

import hashlib
import time
from typing import Any

from app.services.model_routing import analytics
from app.services.model_routing.detection import detect_request_type
from app.services.model_routing.model_registry import get_model_registry, reset_model_registry
from app.services.model_routing.models import ALL_REQUEST_TYPES, RoutingDecision, RoutingPlan
from app.services.model_routing.rules import list_rules, preferred_providers
from app.services.model_routing.scoring import composite_score
from app.services.model_routing.version import ENGINE_LABEL, ENGINE_NAME, ENGINE_VERSION


def _plan_id(prompt: str, rtype: str) -> str:
    digest = hashlib.sha1(f"{rtype}|{prompt[:80]}|{time.time_ns()}".encode()).hexdigest()
    return f"rplan_{digest[:12]}"


def _unavailable_providers() -> set[str]:
    """Optional sync with orchestration statuses when available."""
    try:
        from app.services.provider_orchestration.manager import get_provider_manager

        mgr = get_provider_manager()
        bad: set[str] = set()
        for p in mgr.registry.all():
            st = p.get_status()
            if st in ("offline", "disabled", "maintenance"):
                bad.add(p.provider_id)
        return bad
    except Exception:
        return set()


def select_route(
    prompt: str,
    *,
    request_type: str | None = None,
    strategy: str = "balanced",
    prefer_cheap: bool | None = None,
    provider_hint: str | None = None,
    failover: bool = True,
    load_balance: bool = True,
) -> RoutingPlan:
    text = (prompt or "").strip()
    if not text and not request_type:
        raise ValueError("prompt or request_type is required")

    rtype, confidence, notes = detect_request_type(text or " ", hint=request_type)
    registry = get_model_registry()
    preferred = preferred_providers(rtype)
    unavailable = _unavailable_providers()

    # Strategy weights
    strat = (strategy or "balanced").lower()
    weights = {
        "balanced": {"cost": 0.2, "latency": 0.25, "quality": 0.35, "load": 0.2},
        "cost": {"cost": 0.55, "latency": 0.15, "quality": 0.2, "load": 0.1},
        "latency": {"cost": 0.1, "latency": 0.55, "quality": 0.2, "load": 0.15},
        "quality": {"cost": 0.1, "latency": 0.15, "quality": 0.6, "load": 0.15},
        "load": {"cost": 0.15, "latency": 0.2, "quality": 0.25, "load": 0.4},
    }.get(strat, {"cost": 0.2, "latency": 0.25, "quality": 0.35, "load": 0.2})
    cheap = prefer_cheap if prefer_cheap is not None else strat == "cost"

    candidates = registry.for_type(rtype)
    if provider_hint:
        hinted = [m for m in candidates if m.provider_id == provider_hint.strip().lower()]
        if hinted:
            candidates = hinted + [m for m in candidates if m not in hinted]

    # Prefer rule order, then score within/across
    scored: list[tuple[float, Any, dict[str, float], int]] = []
    for entry in candidates:
        if entry.provider_id in unavailable and failover:
            continue
        metrics = composite_score(entry, weights=weights, prefer_cheap=cheap)
        # Rule preference bonus
        try:
            rule_rank = preferred.index(entry.provider_id)
            # Strong rule preference so declared defaults (e.g. Image→Stability) win
            rule_bonus = max(0.0, (len(preferred) - rule_rank) / max(1, len(preferred))) * 0.45
        except ValueError:
            rule_rank = 99
            rule_bonus = 0.0
        # Load balancing: slightly perturb by load when enabled
        load_adj = (1.0 - entry.load) * 0.03 if load_balance else 0.0
        total = metrics["overall"] + rule_bonus + load_adj
        scored.append((total, entry, metrics, rule_rank))

    if not scored:
        # Absolute fallback to simulation
        sim = registry.for_provider("simulation", rtype)
        if not sim:
            raise ValueError(f"No models available for request type: {rtype}")
        entry = sim[0]
        metrics = composite_score(entry, weights=weights, prefer_cheap=cheap)
        scored = [(metrics["overall"], entry, metrics, 0)]

    scored.sort(key=lambda x: (-x[0], x[3], x[1].priority))
    best_score, best, best_metrics, _ = scored[0]

    # Build failover / fallback chain
    chain: list[dict[str, str]] = []
    seen = {best.provider_id}
    for total, entry, _m, _r in scored[1:]:
        if entry.provider_id in seen:
            continue
        seen.add(entry.provider_id)
        chain.append({"provider": entry.provider_id, "model": entry.model_id})
        if len(chain) >= 4:
            break
    # Ensure rule fallbacks appear
    if failover:
        for pid in preferred:
            if pid == best.provider_id or pid in seen:
                continue
            models = registry.for_provider(pid, rtype)
            if models and pid not in unavailable:
                chain.append({"provider": pid, "model": models[0].model_id})
                seen.add(pid)
            if len(chain) >= 5:
                break

    reasons = [
        f"detected={rtype}",
        f"strategy={strat}",
        f"rule_primary={preferred[0] if preferred else 'n/a'}",
        *notes[:4],
    ]
    if best.provider_id == (preferred[0] if preferred else None):
        reasons.append("matched_routing_rule")

    decision = RoutingDecision(
        request_type=rtype,
        primary_provider=best.provider_id,
        primary_model=best.model_id,
        fallback_chain=chain,
        strategy=strat,
        score=round(min(100.0, max(0.0, best_score * 100.0)), 2),
        cost_score=round(best_metrics["cost_score"] * 100.0, 2),
        latency_score=round(best_metrics["latency_score"] * 100.0, 2),
        quality_score=round(best_metrics["quality_score"] * 100.0, 2),
        load_score=round(best_metrics["load_score"] * 100.0, 2),
        reasons=reasons,
        confidence=confidence,
    )

    analytics_id = analytics.record_routing(
        request_type=rtype,
        provider=best.provider_id,
        model=best.model_id,
        score=decision.score,
        strategy=strat,
        prompt=text,
    )

    return RoutingPlan(
        plan_id=_plan_id(text, rtype),
        prompt=text,
        request_type=rtype,
        decision=decision,
        failover_enabled=failover,
        load_balanced=load_balance,
        analytics_id=analytics_id,
    )


def plan_route(prompt: str, **kwargs: Any) -> dict[str, Any]:
    plan = select_route(prompt, **kwargs)
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
        "operation": "plan",
        **plan.to_dict(),
        "rules": list_rules().get(plan.request_type),
    }


def select_provider(prompt: str, **kwargs: Any) -> dict[str, Any]:
    plan = select_route(prompt, **kwargs)
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
        "operation": "select",
        "request_type": plan.request_type,
        "provider": plan.decision.primary_provider,
        "model": plan.decision.primary_model,
        "fallback_chain": plan.decision.fallback_chain,
        "score": plan.decision.score,
        "confidence": plan.decision.confidence,
        "strategy": plan.decision.strategy,
        "reasons": plan.decision.reasons,
        "analytics_id": plan.analytics_id,
        "plan_id": plan.plan_id,
    }


def list_models() -> dict[str, Any]:
    reg = get_model_registry()
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
        **reg.list_payload(),
        "rules": list_rules(),
    }


def router_status() -> dict[str, Any]:
    reg = get_model_registry()
    stats = analytics.summary(limit=200)
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
        "model_count": len(reg.all()),
        "provider_count": len(reg.list_payload()["providers"]),
        "request_types": list(ALL_REQUEST_TYPES),
        "analytics": {
            "count": stats["count"],
            "avg_score": stats["avg_score"],
            "by_request_type": stats["by_request_type"],
            "by_provider": stats["by_provider"],
        },
        "failover_enabled": True,
        "load_balancing_enabled": True,
        "strategies": ["balanced", "cost", "latency", "quality", "load"],
        "ok": True,
    }


def plan_dict(**kwargs: Any) -> dict[str, Any]:
    prompt = kwargs.pop("prompt", None)
    if prompt is None:
        raise ValueError("prompt is required")
    return plan_route(prompt, **kwargs)


def select_dict(**kwargs: Any) -> dict[str, Any]:
    prompt = kwargs.pop("prompt", None)
    if prompt is None:
        raise ValueError("prompt is required")
    return select_provider(prompt, **kwargs)


def reset_routing() -> None:
    reset_model_registry()
    analytics.clear()
