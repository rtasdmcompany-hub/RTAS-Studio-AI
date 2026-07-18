"""Daily / Monthly / Project / Team usage reports."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.services.cost_intelligence import store
from app.services.cost_intelligence.models import ReportPeriod, UsageReport, new_id


def _filter_events(
    *,
    period: ReportPeriod,
    scope_id: str | None = None,
) -> list:
    events = store.all_events()
    now = datetime.now(timezone.utc)
    filtered = []
    for e in events:
        if period == "project" and scope_id and e.project_id != scope_id:
            continue
        if period == "team" and scope_id and e.team_id != scope_id:
            continue
        if period in ("daily", "monthly"):
            try:
                created = datetime.fromisoformat(e.created_at.replace("Z", "+00:00"))
            except ValueError:
                created = now
            delta = now - created
            if period == "daily" and delta.total_seconds() > 86400:
                continue
            if period == "monthly" and delta.days > 31:
                continue
        filtered.append(e)
    return filtered


def _rollup(events: list) -> tuple[float, float, int, list[dict[str, Any]]]:
    by_prov: dict[str, dict[str, Any]] = {}
    total_cost = 0.0
    total_credits = 0.0
    for e in events:
        total_cost += e.cost_usd
        total_credits += e.credits
        row = by_prov.setdefault(
            e.provider,
            {"provider": e.provider, "requests": 0, "cost_usd": 0.0, "credits": 0.0, "tokens": 0},
        )
        row["requests"] += 1
        row["cost_usd"] += e.cost_usd
        row["credits"] += e.credits
        row["tokens"] += e.tokens
    for row in by_prov.values():
        row["cost_usd"] = round(row["cost_usd"], 6)
        row["credits"] = round(row["credits"], 4)
    return total_cost, total_credits, len(events), list(by_prov.values())


def generate_report(
    period: ReportPeriod,
    *,
    scope_id: str | None = None,
) -> UsageReport:
    events = _filter_events(period=period, scope_id=scope_id)
    total_cost, total_credits, total_requests, by_provider = _rollup(events)
    report = UsageReport(
        report_id=new_id("report"),
        period=period,
        scope_id=scope_id,
        total_cost_usd=round(total_cost, 6),
        total_credits=round(total_credits, 4),
        total_requests=total_requests,
        by_provider=by_provider,
        metadata={"event_count": len(events)},
    )
    return store.save_report(report)


def daily_report() -> dict[str, Any]:
    return generate_report("daily").to_dict()


def monthly_report() -> dict[str, Any]:
    return generate_report("monthly").to_dict()


def project_report(project_id: str) -> dict[str, Any]:
    return generate_report("project", scope_id=project_id).to_dict()


def team_report(team_id: str) -> dict[str, Any]:
    return generate_report("team", scope_id=team_id).to_dict()
