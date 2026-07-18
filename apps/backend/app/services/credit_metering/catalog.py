"""AI service credit costs, provider rates, quota defaults, fair-usage policy."""

from __future__ import annotations

from typing import Any, Final

SERVICE_TYPES: Final[tuple[str, ...]] = (
    "image_generation",
    "video_generation",
    "audio_generation",
    "voice_cloning",
    "ai_upscaling",
    "image_editing",
    "video_editing",
    "background_removal",
    "future_ai_service",
)

# Base credits charged per unit request (quantity=1)
SERVICE_CREDIT_COSTS: Final[dict[str, int]] = {
    "image_generation": 5,
    "video_generation": 40,
    "audio_generation": 8,
    "voice_cloning": 25,
    "ai_upscaling": 6,
    "image_editing": 4,
    "video_editing": 20,
    "background_removal": 3,
    "future_ai_service": 10,
}

# Estimated USD provider cost per credit unit (for margin math)
PROVIDER_COST_PER_CREDIT_USD: Final[dict[str, float]] = {
    "fal": 0.012,
    "replicate": 0.015,
    "runway": 0.028,
    "kling": 0.022,
    "veo": 0.035,
    "openai": 0.018,
    "internal": 0.004,
    "default": 0.015,
}

# GPU cost estimate USD per credit (amortized)
GPU_COST_PER_CREDIT_USD: Final[float] = 0.003

# Retail credit value USD (what customer effectively pays per credit at pack rates)
RETAIL_CREDIT_VALUE_USD: Final[float] = 0.08

# Plan → quota defaults (credits). None / -1 = unlimited
PLAN_QUOTAS: Final[dict[str, dict[str, Any]]] = {
    "free_trial": {
        "dailyCredits": 50,
        "monthlyCredits": 100,
        "trialCredits": 100,
        "unlimited": False,
    },
    "starter": {
        "dailyCredits": 200,
        "monthlyCredits": 1000,
        "trialCredits": 0,
        "unlimited": False,
    },
    "professional": {
        "dailyCredits": 800,
        "monthlyCredits": 5000,
        "trialCredits": 0,
        "unlimited": False,
    },
    "business": {
        "dailyCredits": 3000,
        "monthlyCredits": 20000,
        "trialCredits": 0,
        "unlimited": False,
    },
    "enterprise": {
        "dailyCredits": -1,
        "monthlyCredits": -1,
        "trialCredits": 0,
        "unlimited": True,
    },
}

# Fair usage: soft/hard burst multipliers vs daily quota
FAIR_USAGE_SOFT_MULTIPLIER: Final[float] = 1.5
FAIR_USAGE_HARD_MULTIPLIER: Final[float] = 2.0
FAIR_USAGE_BURST_WINDOW_MINUTES: Final[int] = 60


def normalize_service(service: str) -> str:
    key = (service or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "image": "image_generation",
        "img": "image_generation",
        "video": "video_generation",
        "audio": "audio_generation",
        "voice": "voice_cloning",
        "clone": "voice_cloning",
        "upscale": "ai_upscaling",
        "upscaling": "ai_upscaling",
        "edit_image": "image_editing",
        "edit_video": "video_editing",
        "bg_remove": "background_removal",
        "background": "background_removal",
        "future": "future_ai_service",
    }
    key = aliases.get(key, key)
    if key not in SERVICE_CREDIT_COSTS:
        raise ValueError(f"unknown AI service type: {service}")
    return key


def credits_for_service(service: str, quantity: float = 1.0) -> int:
    key = normalize_service(service)
    base = SERVICE_CREDIT_COSTS[key]
    qty = max(0.0, float(quantity))
    return max(1, int(round(base * qty))) if qty > 0 else 0


def provider_rate(provider: str | None) -> float:
    key = (provider or "default").strip().lower()
    return float(PROVIDER_COST_PER_CREDIT_USD.get(key, PROVIDER_COST_PER_CREDIT_USD["default"]))


def plan_quota(plan_key: str | None) -> dict[str, Any]:
    key = (plan_key or "free_trial").strip().lower()
    return dict(PLAN_QUOTAS.get(key, PLAN_QUOTAS["free_trial"]))
