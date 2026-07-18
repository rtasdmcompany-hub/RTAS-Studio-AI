"""Automatic Provider Optimization + Cost Optimization."""

from __future__ import annotations

from typing import Any

from app.services.cost_intelligence import store
from app.services.cost_intelligence.models import OptimizeMode, OptimizationDecision, new_id
from app.services.cost_intelligence.pricing import calculate_cost, rates_for
from app.services.cost_intelligence.ranking import rank_providers


def _mode_weights(mode: OptimizeMode) -> dict[str, float]:
    return {
        "cost": {"cost": 0.55, "speed": 0.15, "quality": 0.15, "reliability": 0.15},
        "latency": {"cost": 0.15, "speed": 0.55, "quality": 0.15, "reliability": 0.15},
        "quality": {"cost": 0.15, "speed": 0.15, "quality": 0.55, "reliability": 0.15},
        "balanced": {"cost": 0.30, "speed": 0.25, "quality": 0.25, "reliability": 0.20},
    }.get(mode, {"cost": 0.30, "speed": 0.25, "quality": 0.25, "reliability": 0.20})


def optimize(
    *,
    mode: OptimizeMode = "balanced",
    capability: str | None = None,
    tokens: int = 1000,
    images: int = 0,
    video_sec: float = 0.0,
    audio_sec: float = 0.0,
    voice_sec: float = 0.0,
    prefer_provider: str | None = None,
) -> OptimizationDecision:
    ranked = rank_providers(capability=capability)
    weights = _mode_weights(mode)
    scored: list[tuple[float, Any, float, float]] = []

    for item in ranked:
        # Re-score with mode weights
        s = (
            (item.cost_score / 100.0) * weights["cost"]
            + (item.speed_score / 100.0) * weights["speed"]
            + (item.quality_score / 100.0) * weights["quality"]
            + (item.reliability_score / 100.0) * weights["reliability"]
        )
        if prefer_provider and item.provider == prefer_provider.lower():
            s += 0.05
        breakdown = calculate_cost(
            item.provider,
            tokens=tokens,
            images=images,
            video_sec=video_sec,
            audio_sec=audio_sec,
            voice_sec=voice_sec,
        )
        latency = rates_for(item.provider)["latency_ms"]
        scored.append((s, item, breakdown.total_usd, latency))

    scored.sort(key=lambda x: (-x[0], x[2]))
    best_score, best, best_cost, best_latency = scored[0]
    # Baseline = most expensive among top candidates for savings estimate
    max_cost = max(x[2] for x in scored) if scored else best_cost
    savings = max(0.0, max_cost - best_cost)

    alternatives = []
    for s, item, cost, lat in scored[1:4]:
        alternatives.append(
            {
                "provider": item.provider,
                "score": round(s * 100.0, 2),
                "estimated_cost_usd": round(cost, 6),
                "estimated_latency_ms": lat,
                "reason": item.reason,
            }
        )

    model = None
    # Soft model hint from capability
    if capability in ("text", "chat", "code", None):
        model = {
            "openai": "gpt-4o-mini",
            "gemini": "gemini-1.5-pro",
            "claude": "claude-3-5-sonnet",
        }.get(best.provider)
    elif capability == "image":
        model = {
            "stability": "sdxl",
            "openai": "dall-e-3",
            "fal": "flux-dev",
        }.get(best.provider)
    elif capability in ("voice", "audio"):
        model = "eleven-multilingual-v2" if best.provider == "elevenlabs" else None
    elif capability == "video":
        model = {
            "runpod": "runpod-video-xl",
            "fal": "fal-video",
            "replicate": "replicate-svd",
        }.get(best.provider)

    decision = OptimizationDecision(
        decision_id=new_id("opt"),
        mode=mode,
        selected_provider=best.provider,
        selected_model=model,
        estimated_cost_usd=round(best_cost, 6),
        estimated_latency_ms=best_latency,
        quality_score=best.quality_score,
        savings_usd=round(savings, 6),
        alternatives=alternatives,
        ranking=[r.to_dict() for r in ranked[:8]],
        reason=(
            f"Selected {best.provider} via {mode} optimization "
            f"(score={round(best_score * 100, 2)}; {best.reason})"
        ),
    )
    return store.save_optimization(decision)
