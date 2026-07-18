"""Performance monitoring for cost / provider intelligence."""

from __future__ import annotations

from typing import Any

from app.services.cost_intelligence import store
from app.services.cost_intelligence.models import PROVIDER_CATALOG
from app.services.cost_intelligence.pricing import rates_for


def performance_metrics() -> dict[str, Any]:
    totals = store.all_totals()
    by_project: dict[str, float] = {}
    events = store.all_events()
    for e in events:
        if e.project_id:
            by_project[e.project_id] = by_project.get(e.project_id, 0.0) + e.cost_usd

    total_req = sum(t.requests for t in totals)
    total_ok = sum(t.successes for t in totals)
    total_fail = sum(t.failures for t in totals)
    total_cost = sum(t.processing_cost_usd for t in totals)
    total_latency = sum(t.total_latency_ms for t in totals)

    uptime = {}
    for p in PROVIDER_CATALOG:
        r = rates_for(p)
        t = store.get_totals(p)
        if t and t.requests:
            uptime[p] = round((t.successes / t.requests) * 100.0, 2)
        else:
            uptime[p] = round(r["availability"] * 100.0, 2)

    # Queue efficiency proxy: success rate weighted by inverse latency
    avg_latency = total_latency / total_req if total_req else 0.0
    success_rate = (total_ok / total_req) * 100.0 if total_req else 100.0
    queue_efficiency = round(
        min(100.0, success_rate * (1.0 - min(0.5, avg_latency / 5000.0))),
        2,
    )

    return {
        "average_response_time_ms": round(avg_latency, 2),
        "cost_per_request": round(total_cost / total_req, 6) if total_req else 0.0,
        "cost_per_project": {k: round(v, 6) for k, v in by_project.items()},
        "success_rate": round(success_rate, 2),
        "failure_rate": round((total_fail / total_req) * 100.0, 2) if total_req else 0.0,
        "provider_uptime": uptime,
        "queue_efficiency": queue_efficiency,
        "total_requests": total_req,
        "total_cost_usd": round(total_cost, 6),
    }
