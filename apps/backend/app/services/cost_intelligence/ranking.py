"""Dynamic Provider Ranking."""

from __future__ import annotations

from app.services.cost_intelligence import store
from app.services.cost_intelligence.models import PROVIDER_CATALOG, ProviderRank
from app.services.cost_intelligence.pricing import estimated_cost_per_1k, rates_for
from app.services.cost_intelligence.version import (
    OPTIMIZATION_COST_WEIGHT,
    OPTIMIZATION_QUALITY_WEIGHT,
    OPTIMIZATION_RELIABILITY_WEIGHT,
    OPTIMIZATION_SPEED_WEIGHT,
)


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


def _score_provider(provider: str) -> ProviderRank:
    r = rates_for(provider)
    totals = store.get_totals(provider)
    requests = totals.requests if totals else 0
    success_rate = (
        (totals.successes / requests) * 100.0 if totals and requests else 98.0
    )
    error_rate = (
        (totals.failures / requests) * 100.0 if totals and requests else 2.0
    )
    avg_latency = (
        totals.total_latency_ms / requests if totals and requests else r["latency_ms"]
    )

    cost_unit = estimated_cost_per_1k(provider)
    cost_score = _clamp01(1.0 - (cost_unit / 0.08))
    speed_score = _clamp01(1.0 - (avg_latency / 3000.0))
    availability_score = _clamp01(r["availability"])
    quality_score = _clamp01(r["quality"])
    reliability_score = _clamp01(
        (r["reliability"] * 0.6) + ((success_rate / 100.0) * 0.4)
    )

    composite = (
        cost_score * OPTIMIZATION_COST_WEIGHT
        + speed_score * OPTIMIZATION_SPEED_WEIGHT
        + quality_score * OPTIMIZATION_QUALITY_WEIGHT
        + reliability_score * OPTIMIZATION_RELIABILITY_WEIGHT
        + availability_score * 0.10
    )
    # normalize weights (sum was 1.1 with availability) — rescale lightly
    composite = composite / 1.10

    reason_parts = []
    if cost_score >= 0.75:
        reason_parts.append("low cost")
    if speed_score >= 0.7:
        reason_parts.append("fast")
    if quality_score >= 0.9:
        reason_parts.append("high quality")
    if reliability_score >= 0.9:
        reason_parts.append("reliable")
    reason = ", ".join(reason_parts) or "balanced profile"

    return ProviderRank(
        provider=provider,
        rank=0,
        score=round(composite * 100.0, 2),
        cost_score=round(cost_score * 100.0, 2),
        speed_score=round(speed_score * 100.0, 2),
        availability_score=round(availability_score * 100.0, 2),
        quality_score=round(quality_score * 100.0, 2),
        reliability_score=round(reliability_score * 100.0, 2),
        success_rate=round(success_rate, 2),
        error_rate=round(error_rate, 2),
        estimated_cost_per_1k=round(cost_unit, 6),
        reason=reason,
    )


def rank_providers(*, capability: str | None = None) -> list[ProviderRank]:
    """Rank all providers; optional capability soft-filter via rate card zeros."""
    ranked = [_score_provider(p) for p in PROVIDER_CATALOG]
    if capability:
        cap = capability.lower()
        # Soft preference: demote providers with no media rate for that capability
        for item in ranked:
            r = rates_for(item.provider)
            if cap in ("image", "images") and r["image"] <= 0:
                item.score *= 0.5
            elif cap in ("video", "videos") and r["video_sec"] <= 0:
                item.score *= 0.5
            elif cap in ("voice",) and r["voice_sec"] <= 0:
                item.score *= 0.5
            elif cap in ("audio",) and r["audio_sec"] <= 0 and r["voice_sec"] <= 0:
                item.score *= 0.5
            elif cap in ("text", "tokens", "chat") and r["token_per_1k"] <= 0:
                item.score *= 0.55
    ranked.sort(key=lambda x: (-x.score, x.estimated_cost_per_1k, x.provider))
    for i, item in enumerate(ranked, start=1):
        item.rank = i
        item.score = round(item.score, 2)
    return ranked
