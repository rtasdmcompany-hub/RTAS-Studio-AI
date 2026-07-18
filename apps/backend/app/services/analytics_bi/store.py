"""Thread-safe in-memory store for analytics & BI."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Iterator

from app.services.analytics_bi.version import MAX_ANALYTICS, MAX_FORECASTS, MAX_REPORTS

if TYPE_CHECKING:
    from app.services.analytics_bi.models import (
        AnalyticsRecord,
        BusinessMetric,
        ForecastRecord,
        KpiRecord,
        PerformanceStatistic,
        ReportHistory,
        UsageStatistic,
    )

_lock = threading.RLock()
_analytics: OrderedDict[str, "AnalyticsRecord"] = OrderedDict()
_business: OrderedDict[str, "BusinessMetric"] = OrderedDict()
_kpis: OrderedDict[str, "KpiRecord"] = OrderedDict()
_reports: OrderedDict[str, "ReportHistory"] = OrderedDict()
_usage: OrderedDict[str, "UsageStatistic"] = OrderedDict()
_perf: OrderedDict[str, "PerformanceStatistic"] = OrderedDict()
_forecasts: OrderedDict[str, "ForecastRecord"] = OrderedDict()

# org-scoped usage counters for fast aggregation
_counters: dict[str, dict[str, float]] = {}
_cache: dict[str, tuple[float, Any]] = {}

_api_timings: list[float] = []
_query_timings: list[float] = []
_report_timings: list[float] = []
_api_count = 0
_error_count = 0
_cache_hits = 0
_cache_misses = 0


def reset_store() -> None:
    global _api_count, _error_count, _cache_hits, _cache_misses
    with _lock:
        _analytics.clear()
        _business.clear()
        _kpis.clear()
        _reports.clear()
        _usage.clear()
        _perf.clear()
        _forecasts.clear()
        _counters.clear()
        _cache.clear()
        _api_timings.clear()
        _query_timings.clear()
        _report_timings.clear()
        _api_count = 0
        _error_count = 0
        _cache_hits = 0
        _cache_misses = 0


@contextmanager
def timed_op(bucket: str = "api") -> Iterator[None]:
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
            if bucket == "query":
                _query_timings.append(ms)
                if len(_query_timings) > 500:
                    del _query_timings[: len(_query_timings) - 500]
            elif bucket == "report":
                _report_timings.append(ms)
                if len(_report_timings) > 500:
                    del _report_timings[: len(_report_timings) - 500]
            else:
                _api_timings.append(ms)
                if len(_api_timings) > 500:
                    del _api_timings[: len(_api_timings) - 500]
            _api_count += 1


def record_error() -> None:
    global _error_count
    with _lock:
        _error_count += 1


def cache_get(key: str) -> Any | None:
    global _cache_hits, _cache_misses
    with _lock:
        item = _cache.get(key)
        if item is None:
            _cache_misses += 1
            return None
        expires, value = item
        if time.time() > expires:
            _cache.pop(key, None)
            _cache_misses += 1
            return None
        _cache_hits += 1
        return value


def cache_set(key: str, value: Any, ttl_sec: float) -> None:
    with _lock:
        _cache[key] = (time.time() + ttl_sec, value)


def bump(org_id: str, key: str, amount: float = 1.0) -> None:
    with _lock:
        bucket = _counters.setdefault(org_id, {})
        bucket[key] = bucket.get(key, 0.0) + amount


def get_counters(org_id: str) -> dict[str, float]:
    with _lock:
        return dict(_counters.get(org_id, {}))


def save_analytics(r: "AnalyticsRecord") -> "AnalyticsRecord":
    with _lock:
        _analytics[r.id] = r
        while len(_analytics) > MAX_ANALYTICS:
            _analytics.popitem(last=False)
        return r


def list_analytics(
    *,
    organization_id: str,
    category: str | None = None,
    workspace_id: str | None = None,
) -> list["AnalyticsRecord"]:
    with _lock:
        items = [r for r in _analytics.values() if r.organization_id == organization_id]
    if category:
        items = [r for r in items if r.category == category]
    if workspace_id:
        items = [r for r in items if r.workspace_id == workspace_id]
    items.sort(key=lambda r: r.recorded_at, reverse=True)
    return items


def save_business(m: "BusinessMetric") -> "BusinessMetric":
    with _lock:
        _business[m.id] = m
        return m


def list_business(organization_id: str) -> list["BusinessMetric"]:
    with _lock:
        items = [m for m in _business.values() if m.organization_id == organization_id]
    items.sort(key=lambda m: m.recorded_at, reverse=True)
    return items


def save_kpi(k: "KpiRecord") -> "KpiRecord":
    with _lock:
        _kpis[k.id] = k
        return k


def list_kpis(organization_id: str, *, workspace_id: str | None = None) -> list["KpiRecord"]:
    with _lock:
        items = [k for k in _kpis.values() if k.organization_id == organization_id]
    if workspace_id:
        items = [k for k in items if k.workspace_id == workspace_id]
    # latest per key
    latest: dict[str, "KpiRecord"] = {}
    for k in sorted(items, key=lambda x: x.recorded_at):
        latest[k.kpi_key] = k
    return list(latest.values())


def save_report(r: "ReportHistory") -> "ReportHistory":
    with _lock:
        _reports[r.id] = r
        while len(_reports) > MAX_REPORTS:
            _reports.popitem(last=False)
        return r


def list_reports(organization_id: str) -> list["ReportHistory"]:
    with _lock:
        items = [r for r in _reports.values() if r.organization_id == organization_id]
    items.sort(key=lambda r: r.created_at, reverse=True)
    return items


def save_usage(u: "UsageStatistic") -> "UsageStatistic":
    with _lock:
        _usage[u.id] = u
        return u


def list_usage(organization_id: str) -> list["UsageStatistic"]:
    with _lock:
        return [u for u in _usage.values() if u.organization_id == organization_id]


def save_perf(p: "PerformanceStatistic") -> "PerformanceStatistic":
    with _lock:
        _perf[p.id] = p
        return p


def list_perf(organization_id: str) -> list["PerformanceStatistic"]:
    with _lock:
        return [p for p in _perf.values() if p.organization_id == organization_id]


def save_forecast(f: "ForecastRecord") -> "ForecastRecord":
    with _lock:
        _forecasts[f.id] = f
        while len(_forecasts) > MAX_FORECASTS:
            _forecasts.popitem(last=False)
        return f


def list_forecasts(organization_id: str) -> list["ForecastRecord"]:
    with _lock:
        items = [f for f in _forecasts.values() if f.organization_id == organization_id]
    items.sort(key=lambda f: f.created_at, reverse=True)
    return items


def metrics() -> dict:
    with _lock:
        def _avg(vals: list[float]) -> float:
            return round(sum(vals) / len(vals), 2) if vals else 0.0

        hits = _cache_hits
        misses = _cache_misses
        total = hits + misses
        return {
            "apiCalls": _api_count,
            "avgLatencyMs": _avg(_api_timings),
            "queryAvgMs": _avg(_query_timings),
            "reportAvgMs": _avg(_report_timings),
            "cacheHitRate": round(hits / total, 4) if total else 0.0,
            "cacheHits": hits,
            "cacheMisses": misses,
            "errorRate": round(_error_count / max(_api_count, 1), 4),
            "errors": _error_count,
            "analyticsCount": len(_analytics),
            "reportCount": len(_reports),
            "kpiCount": len(_kpis),
            "forecastCount": len(_forecasts),
        }
