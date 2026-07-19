"""Thread-safe in-memory store for marketplace revenue intelligence."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from app.services.marketplace_revenue.models import (
        CreatorStatsRecord,
        CustomerMetricRecord,
        FinancialSummaryRecord,
        ProductMetricRecord,
        RevenueForecastRecord,
        RevenueLedgerRecord,
        SalesEventRecord,
    )

_lock = threading.RLock()

_ledger: OrderedDict[str, "RevenueLedgerRecord"] = OrderedDict()
_sales: OrderedDict[str, "SalesEventRecord"] = OrderedDict()
_product_metrics: OrderedDict[str, "ProductMetricRecord"] = OrderedDict()
_creators: OrderedDict[str, "CreatorStatsRecord"] = OrderedDict()
_customers: OrderedDict[str, "CustomerMetricRecord"] = OrderedDict()
_forecasts: OrderedDict[str, "RevenueForecastRecord"] = OrderedDict()
_summaries: OrderedDict[str, "FinancialSummaryRecord"] = OrderedDict()

_op_timings: list[float] = []
_op_count = 0
_error_count = 0


def reset_store() -> None:
    global _op_count, _error_count
    with _lock:
        for coll in (
            _ledger,
            _sales,
            _product_metrics,
            _creators,
            _customers,
            _forecasts,
            _summaries,
        ):
            coll.clear()
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
            "ledgerEntries": len(_ledger),
            "salesEvents": len(_sales),
            "productMetrics": len(_product_metrics),
            "creators": len(_creators),
            "customers": len(_customers),
            "forecasts": len(_forecasts),
            "financialSummaries": len(_summaries),
        }


def save_ledger(row: "RevenueLedgerRecord") -> None:
    with _lock:
        _ledger[row.id] = row


def list_ledger(
    *,
    organization_id: str | None = None,
    workspace_id: str | None = None,
    stream: str | None = None,
    period: str | None = None,
) -> list["RevenueLedgerRecord"]:
    with _lock:
        return [
            r
            for r in _ledger.values()
            if (organization_id is None or r.organization_id == organization_id)
            and (workspace_id is None or r.workspace_id == workspace_id)
            and (stream is None or r.stream == stream)
            and (period is None or r.period == period)
        ]


def save_sale(row: "SalesEventRecord") -> None:
    with _lock:
        _sales[row.id] = row


def list_sales(
    *,
    organization_id: str | None = None,
    workspace_id: str | None = None,
    event_type: str | None = None,
) -> list["SalesEventRecord"]:
    with _lock:
        return [
            r
            for r in _sales.values()
            if (organization_id is None or r.organization_id == organization_id)
            and (workspace_id is None or r.workspace_id == workspace_id)
            and (event_type is None or r.event_type == event_type)
        ]


def save_product_metric(row: "ProductMetricRecord") -> None:
    with _lock:
        _product_metrics[row.id] = row


def list_product_metrics(
    *,
    organization_id: str | None = None,
    product_id: str | None = None,
    metric: str | None = None,
) -> list["ProductMetricRecord"]:
    with _lock:
        return [
            r
            for r in _product_metrics.values()
            if (organization_id is None or r.organization_id == organization_id)
            and (product_id is None or r.product_id == product_id)
            and (metric is None or r.metric == metric)
        ]


def save_creator(row: "CreatorStatsRecord") -> None:
    with _lock:
        _creators[row.id] = row


def get_creator(organization_id: str, creator_id: str) -> "CreatorStatsRecord | None":
    with _lock:
        for row in _creators.values():
            if row.organization_id == organization_id and row.creator_id == creator_id:
                return row
        return None


def list_creators(*, organization_id: str | None = None) -> list["CreatorStatsRecord"]:
    with _lock:
        return [
            r
            for r in _creators.values()
            if organization_id is None or r.organization_id == organization_id
        ]


def save_customer(row: "CustomerMetricRecord") -> None:
    with _lock:
        _customers[row.id] = row


def get_customer(
    organization_id: str, customer_id: str
) -> "CustomerMetricRecord | None":
    with _lock:
        for row in _customers.values():
            if (
                row.organization_id == organization_id
                and row.customer_id == customer_id
            ):
                return row
        return None


def list_customers(
    *, organization_id: str | None = None
) -> list["CustomerMetricRecord"]:
    with _lock:
        return [
            r
            for r in _customers.values()
            if organization_id is None or r.organization_id == organization_id
        ]


def save_forecast(row: "RevenueForecastRecord") -> None:
    with _lock:
        _forecasts[row.id] = row


def list_forecasts(
    *, organization_id: str | None = None
) -> list["RevenueForecastRecord"]:
    with _lock:
        return [
            r
            for r in _forecasts.values()
            if organization_id is None or r.organization_id == organization_id
        ]


def save_summary(row: "FinancialSummaryRecord") -> None:
    with _lock:
        _summaries[row.id] = row


def list_summaries(
    *, organization_id: str | None = None, period: str | None = None
) -> list["FinancialSummaryRecord"]:
    with _lock:
        return [
            r
            for r in _summaries.values()
            if (organization_id is None or r.organization_id == organization_id)
            and (period is None or r.period == period)
        ]
