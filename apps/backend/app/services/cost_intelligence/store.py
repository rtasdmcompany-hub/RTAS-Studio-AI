"""Thread-safe in-memory store for usage, budgets, and optimization history."""

from __future__ import annotations

import threading
from collections import OrderedDict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.cost_intelligence.models import (
        BudgetProfile,
        OptimizationDecision,
        ProviderUsageTotals,
        UsageEvent,
        UsageReport,
    )

_lock = threading.Lock()
_events: OrderedDict[str, "UsageEvent"] = OrderedDict()
_totals: dict[str, "ProviderUsageTotals"] = {}
_budgets: dict[str, "BudgetProfile"] = {}
_optimizations: OrderedDict[str, "OptimizationDecision"] = OrderedDict()
_reports: OrderedDict[str, "UsageReport"] = OrderedDict()
_MAX_EVENTS = 10000
_MAX_OPTS = 2000
_MAX_REPORTS = 2000


def save_event(event: "UsageEvent") -> "UsageEvent":
    with _lock:
        _events[event.event_id] = event
        while len(_events) > _MAX_EVENTS:
            _events.popitem(last=False)
        return event


def all_events() -> list["UsageEvent"]:
    with _lock:
        return list(_events.values())


def get_totals(provider: str) -> "ProviderUsageTotals | None":
    with _lock:
        return _totals.get(provider)


def set_totals(provider: str, totals: "ProviderUsageTotals") -> None:
    with _lock:
        _totals[provider] = totals


def all_totals() -> list["ProviderUsageTotals"]:
    with _lock:
        return list(_totals.values())


def save_budget(budget: "BudgetProfile") -> "BudgetProfile":
    with _lock:
        _budgets[budget.budget_id] = budget
        return budget


def all_budgets() -> list["BudgetProfile"]:
    with _lock:
        return list(_budgets.values())


def get_budget(budget_id: str) -> "BudgetProfile | None":
    with _lock:
        return _budgets.get(budget_id)


def save_optimization(decision: "OptimizationDecision") -> "OptimizationDecision":
    with _lock:
        _optimizations[decision.decision_id] = decision
        while len(_optimizations) > _MAX_OPTS:
            _optimizations.popitem(last=False)
        return decision


def optimization_history(limit: int = 50) -> list["OptimizationDecision"]:
    with _lock:
        items = list(_optimizations.values())
        return list(reversed(items[-max(1, min(500, limit)) :]))


def save_report(report: "UsageReport") -> "UsageReport":
    with _lock:
        _reports[report.report_id] = report
        while len(_reports) > _MAX_REPORTS:
            _reports.popitem(last=False)
        return report


def all_reports(limit: int = 50) -> list["UsageReport"]:
    with _lock:
        items = list(_reports.values())
        return list(reversed(items[-max(1, min(500, limit)) :]))


def clear() -> None:
    with _lock:
        _events.clear()
        _totals.clear()
        _budgets.clear()
        _optimizations.clear()
        _reports.clear()
