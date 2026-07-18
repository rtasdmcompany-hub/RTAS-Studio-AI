"""Thread-safe in-memory store for credit metering & quotas."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from app.services.credit_metering.models import (
        AIUsageHistoryEntry,
        CostCalculation,
        CreditUsageEvent,
        ProviderCostRate,
        UsageMetricBucket,
        UsageQuota,
    )

_lock = threading.RLock()

_usage_events: OrderedDict[str, "CreditUsageEvent"] = OrderedDict()
_metrics: OrderedDict[str, "UsageMetricBucket"] = OrderedDict()
_quotas: OrderedDict[str, "UsageQuota"] = OrderedDict()
_quota_by_scope: dict[str, str] = {}
_ai_history: OrderedDict[str, "AIUsageHistoryEntry"] = OrderedDict()
_cost_calcs: OrderedDict[str, "CostCalculation"] = OrderedDict()
_provider_costs: OrderedDict[str, "ProviderCostRate"] = OrderedDict()

_api_timings: list[float] = []
_api_count = 0
_error_count = 0


def reset_store() -> None:
    global _api_count, _error_count
    with _lock:
        _usage_events.clear()
        _metrics.clear()
        _quotas.clear()
        _quota_by_scope.clear()
        _ai_history.clear()
        _cost_calcs.clear()
        _provider_costs.clear()
        _api_timings.clear()
        _api_count = 0
        _error_count = 0


@contextmanager
def timed_op() -> Iterator[None]:
    global _api_count
    start = time.perf_counter()
    try:
        yield
    except Exception:
        record_error()
        raise
    finally:
        ms = (time.perf_counter() - start) * 1000
        with _lock:
            _api_timings.append(ms)
            if len(_api_timings) > 500:
                del _api_timings[: len(_api_timings) - 500]
            _api_count += 1


def record_error() -> None:
    global _error_count
    with _lock:
        _error_count += 1


def metrics_snapshot() -> dict[str, Any]:
    with _lock:
        timings = list(_api_timings)
        avg = sum(timings) / len(timings) if timings else 0.0
        return {
            "apiCount": _api_count,
            "errorCount": _error_count,
            "avgLatencyMs": round(avg, 3),
            "usageEvents": len(_usage_events),
            "metricBuckets": len(_metrics),
            "quotas": len(_quotas),
            "aiHistory": len(_ai_history),
            "costCalculations": len(_cost_calcs),
        }


def _scope_key(
    organization_id: str,
    workspace_id: str | None = None,
    team_id: str | None = None,
) -> str:
    return f"{organization_id}|{workspace_id or ''}|{team_id or ''}"


def save_usage(event: "CreditUsageEvent") -> None:
    with _lock:
        _usage_events[event.id] = event


def list_usage(
    organization_id: str,
    *,
    workspace_id: str | None = None,
    user_id: str | None = None,
    limit: int = 100,
) -> list["CreditUsageEvent"]:
    with _lock:
        items = [
            e
            for e in _usage_events.values()
            if e.organization_id == organization_id
            and (workspace_id is None or e.workspace_id == workspace_id)
            and (user_id is None or e.user_id == user_id)
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


def save_metric(bucket: "UsageMetricBucket") -> None:
    with _lock:
        _metrics[bucket.id] = bucket


def get_metric(metric_id: str) -> "UsageMetricBucket | None":
    with _lock:
        return _metrics.get(metric_id)


def find_metric(
    *,
    organization_id: str,
    period: str,
    period_key: str,
    workspace_id: str | None = None,
    user_id: str | None = None,
    provider: str | None = None,
) -> "UsageMetricBucket | None":
    with _lock:
        for b in _metrics.values():
            if (
                b.organization_id == organization_id
                and b.period == period
                and b.period_key == period_key
                and b.workspace_id == workspace_id
                and b.user_id == user_id
                and b.provider == provider
            ):
                return b
        return None


def list_metrics(
    organization_id: str,
    *,
    period: str | None = None,
    limit: int = 200,
) -> list["UsageMetricBucket"]:
    with _lock:
        items = [
            b
            for b in _metrics.values()
            if b.organization_id == organization_id
            and (period is None or b.period == period)
        ]
        items.sort(key=lambda x: x.updated_at, reverse=True)
        return items[:limit]


def save_quota(quota: "UsageQuota") -> None:
    with _lock:
        _quotas[quota.id] = quota
        _quota_by_scope[
            _scope_key(quota.organization_id, quota.workspace_id, quota.team_id)
        ] = quota.id


def get_quota_by_scope(
    organization_id: str,
    workspace_id: str | None = None,
    team_id: str | None = None,
) -> "UsageQuota | None":
    with _lock:
        qid = _quota_by_scope.get(_scope_key(organization_id, workspace_id, team_id))
        return _quotas.get(qid) if qid else None


def save_ai_history(entry: "AIUsageHistoryEntry") -> None:
    with _lock:
        _ai_history[entry.id] = entry


def list_ai_history(
    organization_id: str, *, limit: int = 100
) -> list["AIUsageHistoryEntry"]:
    with _lock:
        items = [h for h in _ai_history.values() if h.organization_id == organization_id]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


def save_cost(calc: "CostCalculation") -> None:
    with _lock:
        _cost_calcs[calc.id] = calc


def list_costs(organization_id: str, *, limit: int = 100) -> list["CostCalculation"]:
    with _lock:
        items = [c for c in _cost_calcs.values() if c.organization_id == organization_id]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


def save_provider_cost(rate: "ProviderCostRate") -> None:
    with _lock:
        _provider_costs[rate.provider] = rate


def get_provider_cost(provider: str) -> "ProviderCostRate | None":
    with _lock:
        return _provider_costs.get(provider)


def list_provider_costs() -> list["ProviderCostRate"]:
    with _lock:
        return list(_provider_costs.values())
