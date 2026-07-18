"""Provider Analytics Engine."""

from __future__ import annotations

from typing import Any

from app.services.cost_intelligence import credit_tracker, store, token_tracker
from app.services.cost_intelligence.models import PROVIDER_CATALOG, ProviderUsageTotals
from app.services.cost_intelligence.pricing import rates_for


def ensure_provider_totals() -> None:
    for p in PROVIDER_CATALOG:
        if store.get_totals(p) is None:
            store.set_totals(p, ProviderUsageTotals(provider=p))


def apply_event_to_totals(
    provider: str,
    *,
    tokens: int = 0,
    images: int = 0,
    videos: int = 0,
    audio: int = 0,
    voice: int = 0,
    storage_mb: float = 0.0,
    gpu_time_sec: float = 0.0,
    cost_usd: float = 0.0,
    credits: float = 0.0,
    latency_ms: float = 0.0,
    success: bool = True,
) -> ProviderUsageTotals:
    ensure_provider_totals()
    key = provider.lower()
    t = store.get_totals(key) or ProviderUsageTotals(provider=key)
    t.requests += 1
    t.tokens += max(0, tokens)
    t.images += max(0, images)
    t.videos += max(0, videos)
    t.audio += max(0, audio)
    t.voice += max(0, voice)
    t.storage_mb += max(0.0, storage_mb)
    t.gpu_time_sec += max(0.0, gpu_time_sec)
    t.processing_cost_usd += max(0.0, cost_usd)
    t.credits += max(0.0, credits)
    t.total_latency_ms += max(0.0, latency_ms)
    if success:
        t.successes += 1
    else:
        t.failures += 1
    store.set_totals(key, t)
    return t


def provider_analytics() -> dict[str, Any]:
    ensure_provider_totals()
    rows = [t.to_dict() for t in store.all_totals()]
    rows.sort(key=lambda r: (-r["processing_cost"], r["provider"]))
    total_cost = sum(r["processing_cost"] for r in rows)
    total_req = sum(r["requests"] for r in rows)
    total_ok = sum(
        int(round(r["requests"] * r["success_rate"] / 100.0)) for r in rows
    )
    return {
        "providers": rows,
        "aggregate": {
            "providers": len(rows),
            "requests": total_req,
            "processing_cost": round(total_cost, 6),
            "tokens": token_tracker.total(),
            "credits": credit_tracker.summary()["total_credits"],
            "success_rate": round((total_ok / total_req) * 100.0, 2) if total_req else 100.0,
            "avg_cost_per_request": round(total_cost / total_req, 6) if total_req else 0.0,
        },
        "rate_card": {p: rates_for(p) for p in PROVIDER_CATALOG},
    }
