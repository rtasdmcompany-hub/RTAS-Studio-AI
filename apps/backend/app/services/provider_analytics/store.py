"""Thread-safe in-memory store for provider analytics, budgets, and profit data."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from app.services.provider_analytics.models import (
        BudgetEvent,
        BudgetPolicy,
        OptimizationRecord,
        ProfitReport,
        ProviderUsageEvent,
    )

_lock = threading.RLock()

_usage_events: OrderedDict[str, "ProviderUsageEvent"] = OrderedDict()
_budget_policies: dict[tuple[str, str], "BudgetPolicy"] = {}
_budget_events: OrderedDict[str, "BudgetEvent"] = OrderedDict()
_profit_reports: OrderedDict[str, "ProfitReport"] = OrderedDict()
_optimizations: OrderedDict[str, "OptimizationRecord"] = OrderedDict()
_custom_providers: dict[str, dict[str, Any]] = {}

_op_timings: list[float] = []
_op_count = 0
_error_count = 0


def reset_store() -> None:
    global _op_count, _error_count
    with _lock:
        _usage_events.clear()
        _budget_policies.clear()
        _budget_events.clear()
        _profit_reports.clear()
        _optimizations.clear()
        _custom_providers.clear()
        _op_timings.clear()
        _op_count = 0
        _error_count = 0


def record_error() -> None:
    global _error_count
    with _lock:
        _error_count += 1


@contextmanager
def timed_op() -> Iterator[None]:
    global _op_count
    start = time.perf_counter()
    try:
        yield
    except Exception:
        record_error()
        raise
    finally:
        ms = (time.perf_counter() - start) * 1000
        with _lock:
            _op_timings.append(ms)
            if len(_op_timings) > 500:
                del _op_timings[: len(_op_timings) - 500]
            _op_count += 1


def metrics() -> dict[str, Any]:
    with _lock:
        timings = list(_op_timings)
        avg = sum(timings) / len(timings) if timings else 0.0
        return {
            "opCount": _op_count,
            "errorCount": _error_count,
            "avgLatencyMs": round(avg, 3),
            "usageEvents": len(_usage_events),
            "budgetPolicies": len(_budget_policies),
            "budgetEvents": len(_budget_events),
            "profitReports": len(_profit_reports),
            "optimizations": len(_optimizations),
            "customProviders": len(_custom_providers),
        }


# --- Usage events ---


def save_usage_event(event: "ProviderUsageEvent") -> None:
    with _lock:
        _usage_events[event.id] = event
        if len(_usage_events) > 100_000:
            _usage_events.popitem(last=False)


def list_usage_events(
    organization_id: str | None = None,
    *,
    provider: str | None = None,
    workspace_id: str | None = None,
    user_id: str | None = None,
    limit: int = 100_000,
) -> list["ProviderUsageEvent"]:
    with _lock:
        items = [
            e
            for e in _usage_events.values()
            if (organization_id is None or e.organization_id == organization_id)
            and (provider is None or e.provider == provider)
            and (workspace_id is None or e.workspace_id == workspace_id)
            and (user_id is None or e.user_id == user_id)
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


# --- Budget policies & events ---


def save_budget_policy(policy: "BudgetPolicy") -> None:
    with _lock:
        _budget_policies[(policy.scope, policy.scope_id)] = policy


def get_budget_policy(scope: str, scope_id: str) -> "BudgetPolicy | None":
    with _lock:
        return _budget_policies.get((scope, scope_id))


def list_budget_policies(organization_id: str) -> list["BudgetPolicy"]:
    with _lock:
        return [
            p for p in _budget_policies.values() if p.organization_id == organization_id
        ]


def save_budget_event(event: "BudgetEvent") -> None:
    with _lock:
        _budget_events[event.id] = event


def list_budget_events(
    organization_id: str, *, event_type: str | None = None, limit: int = 200
) -> list["BudgetEvent"]:
    with _lock:
        items = [
            e
            for e in _budget_events.values()
            if e.organization_id == organization_id
            and (event_type is None or e.event_type == event_type)
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


# --- Profit reports ---


def save_profit_report(report: "ProfitReport") -> None:
    with _lock:
        _profit_reports[report.id] = report


def list_profit_reports(organization_id: str, *, limit: int = 100) -> list["ProfitReport"]:
    with _lock:
        items = [
            r for r in _profit_reports.values() if r.organization_id == organization_id
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


# --- Optimization history ---


def save_optimization(record: "OptimizationRecord") -> None:
    with _lock:
        _optimizations[record.id] = record


def list_optimizations(
    organization_id: str, *, limit: int = 100
) -> list["OptimizationRecord"]:
    with _lock:
        items = [
            o for o in _optimizations.values() if o.organization_id == organization_id
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


# --- Custom providers ---


def save_custom_provider(name: str, profile: dict[str, Any]) -> None:
    with _lock:
        _custom_providers[name] = dict(profile)


def get_custom_provider(name: str) -> dict[str, Any] | None:
    with _lock:
        profile = _custom_providers.get(name)
        return dict(profile) if profile else None


def list_custom_providers() -> dict[str, dict[str, Any]]:
    with _lock:
        return {k: dict(v) for k, v in _custom_providers.items()}
