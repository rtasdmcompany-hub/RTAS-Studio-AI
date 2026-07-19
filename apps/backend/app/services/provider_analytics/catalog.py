"""AI provider profiles, cost components, budget and optimization policies."""

from __future__ import annotations

from typing import Any, Final

# Individually tracked AI providers. New providers can be registered at runtime.
AI_PROVIDERS: Final[dict[str, dict[str, Any]]] = {
    "openai": {
        "label": "OpenAI",
        "costPerRequestUsd": 0.0450,
        "avgLatencyMs": 2400.0,
        "qualityScore": 9.4,
        "capabilities": ["text", "image", "audio"],
    },
    "fal": {
        "label": "fal.ai",
        "costPerRequestUsd": 0.0210,
        "avgLatencyMs": 1500.0,
        "qualityScore": 8.8,
        "capabilities": ["image", "video"],
    },
    "runpod": {
        "label": "RunPod",
        "costPerRequestUsd": 0.0170,
        "avgLatencyMs": 3200.0,
        "qualityScore": 8.2,
        "capabilities": ["image", "video", "gpu"],
    },
    "gemini": {
        "label": "Google Gemini",
        "costPerRequestUsd": 0.0320,
        "avgLatencyMs": 1900.0,
        "qualityScore": 9.0,
        "capabilities": ["text", "image", "video"],
    },
    "anthropic": {
        "label": "Anthropic Claude",
        "costPerRequestUsd": 0.0400,
        "avgLatencyMs": 2100.0,
        "qualityScore": 9.5,
        "capabilities": ["text"],
    },
}

# Cost components tracked per generation (USD baselines)
COST_COMPONENTS: Final[tuple[str, ...]] = (
    "provider",
    "gpu",
    "api",
    "storage",
    "bandwidth",
    "rendering",
)

DEFAULT_COMPONENT_COSTS_USD: Final[dict[str, float]] = {
    "gpu": 0.0080,
    "api": 0.0012,
    "storage": 0.0006,
    "bandwidth": 0.0009,
    "rendering": 0.0040,
}

# Retail value of one credit (revenue side), consistent with credit_metering
CREDIT_RETAIL_VALUE_USD: Final[float] = 0.05

# Fixed monthly platform overhead used in operating-cost estimates
MONTHLY_FIXED_OVERHEAD_USD: Final[float] = 450.0

BUDGET_PERIODS: Final[tuple[str, ...]] = ("daily", "monthly")
BUDGET_SCOPES: Final[tuple[str, ...]] = ("organization", "workspace")

# Alert thresholds as fraction of budget spent
BUDGET_ALERT_THRESHOLDS: Final[tuple[float, ...]] = (0.5, 0.8, 0.95)

BUDGET_EVENT_TYPES: Final[tuple[str, ...]] = (
    "threshold_alert",
    "limit_reached",
    "budget_updated",
    "spend_recorded",
)

OPTIMIZATION_MODES: Final[tuple[str, ...]] = (
    "lowest_cost",
    "fastest",
    "best_quality",
    "balanced",
)

USAGE_STATUSES: Final[tuple[str, ...]] = ("success", "failed")


def provider_profile(provider: str) -> dict[str, Any] | None:
    profile = AI_PROVIDERS.get(provider)
    return dict(profile) if profile else None
