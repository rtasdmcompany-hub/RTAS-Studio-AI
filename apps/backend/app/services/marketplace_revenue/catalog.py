"""Revenue streams, product metrics, forecast horizons, and health scoring."""

from __future__ import annotations

from typing import Final

REVENUE_STREAMS: Final[tuple[str, ...]] = (
    "subscription",
    "marketplace",
    "credit_sales",
    "refund",
)

SALE_EVENT_TYPES: Final[tuple[str, ...]] = (
    "purchase",
    "subscription",
    "credit_pack",
    "refund",
)

PRODUCT_METRICS: Final[tuple[str, ...]] = (
    "view",
    "download",
    "purchase",
    "search_impression",
    "feature",
)

FORECAST_HORIZONS: Final[tuple[str, ...]] = ("30d", "90d", "180d", "365d")

CATEGORIES: Final[tuple[str, ...]] = (
    "video",
    "image",
    "audio",
    "template",
    "prompt",
    "workflow",
    "other",
)


def clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def growth_rate(current: float, previous: float) -> float:
    if previous <= 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100.0, 2)


def marketplace_health_score(
    *,
    conversion_rate: float,
    avg_rating: float,
    churn_rate: float,
    revenue_growth: float,
) -> float:
    """Composite 0–100 marketplace health score."""
    conversion_component = clamp(conversion_rate * 10.0)  # 10% conv => 100
    rating_component = clamp((avg_rating / 5.0) * 100.0)
    retention_component = clamp(100.0 - (churn_rate * 5.0))
    growth_component = clamp(50.0 + revenue_growth)
    score = (
        conversion_component * 0.3
        + rating_component * 0.25
        + retention_component * 0.25
        + growth_component * 0.2
    )
    return round(clamp(score), 2)


def simple_forecast(history: list[float], periods: int = 3) -> list[float]:
    """Linear trend extrapolation from monthly history."""
    if not history:
        return [0.0] * periods
    if len(history) == 1:
        return [round(history[0], 2)] * periods
    # Average delta of last up to 6 points
    window = history[-6:]
    deltas = [window[i] - window[i - 1] for i in range(1, len(window))]
    avg_delta = sum(deltas) / len(deltas)
    last = history[-1]
    out: list[float] = []
    for i in range(1, periods + 1):
        out.append(round(max(0.0, last + avg_delta * i), 2))
    return out
