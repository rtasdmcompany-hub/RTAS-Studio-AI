"""Cost Calculator — unit rates per provider and usage kind."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Baseline enterprise rate card (USD). Tuned for optimization demos + production defaults.
PROVIDER_RATES: dict[str, dict[str, float]] = {
    "openai": {
        "token_per_1k": 0.005,
        "image": 0.04,
        "video_sec": 0.05,
        "audio_sec": 0.006,
        "voice_sec": 0.02,
        "storage_mb": 0.0001,
        "gpu_sec": 0.0,
        "request_base": 0.0002,
        "quality": 0.94,
        "availability": 0.99,
        "reliability": 0.97,
        "latency_ms": 350,
    },
    "gemini": {
        "token_per_1k": 0.003,
        "image": 0.02,
        "video_sec": 0.04,
        "audio_sec": 0.005,
        "voice_sec": 0.018,
        "storage_mb": 0.0001,
        "gpu_sec": 0.0,
        "request_base": 0.00015,
        "quality": 0.90,
        "availability": 0.98,
        "reliability": 0.95,
        "latency_ms": 400,
    },
    "claude": {
        "token_per_1k": 0.006,
        "image": 0.03,
        "video_sec": 0.0,
        "audio_sec": 0.0,
        "voice_sec": 0.0,
        "storage_mb": 0.0001,
        "gpu_sec": 0.0,
        "request_base": 0.00025,
        "quality": 0.93,
        "availability": 0.98,
        "reliability": 0.96,
        "latency_ms": 380,
    },
    "stability": {
        "token_per_1k": 0.0,
        "image": 0.02,
        "video_sec": 0.08,
        "audio_sec": 0.0,
        "voice_sec": 0.0,
        "storage_mb": 0.0002,
        "gpu_sec": 0.01,
        "request_base": 0.001,
        "quality": 0.91,
        "availability": 0.96,
        "reliability": 0.93,
        "latency_ms": 900,
    },
    "elevenlabs": {
        "token_per_1k": 0.0,
        "image": 0.0,
        "video_sec": 0.0,
        "audio_sec": 0.01,
        "voice_sec": 0.018,
        "storage_mb": 0.00015,
        "gpu_sec": 0.0,
        "request_base": 0.0005,
        "quality": 0.95,
        "availability": 0.97,
        "reliability": 0.96,
        "latency_ms": 500,
    },
    "runpod": {
        "token_per_1k": 0.0,
        "image": 0.015,
        "video_sec": 0.035,
        "audio_sec": 0.004,
        "voice_sec": 0.01,
        "storage_mb": 0.00005,
        "gpu_sec": 0.0008,
        "request_base": 0.0008,
        "quality": 0.90,
        "availability": 0.94,
        "reliability": 0.90,
        "latency_ms": 2500,
    },
    "fal": {
        "token_per_1k": 0.0,
        "image": 0.015,
        "video_sec": 0.04,
        "audio_sec": 0.005,
        "voice_sec": 0.012,
        "storage_mb": 0.0001,
        "gpu_sec": 0.001,
        "request_base": 0.0006,
        "quality": 0.89,
        "availability": 0.95,
        "reliability": 0.92,
        "latency_ms": 800,
    },
    "replicate": {
        "token_per_1k": 0.0,
        "image": 0.02,
        "video_sec": 0.045,
        "audio_sec": 0.006,
        "voice_sec": 0.015,
        "storage_mb": 0.00012,
        "gpu_sec": 0.0012,
        "request_base": 0.0007,
        "quality": 0.86,
        "availability": 0.93,
        "reliability": 0.88,
        "latency_ms": 2800,
    },
}

CREDIT_USD = 0.01  # 1 credit ≈ $0.01 processing


@dataclass(frozen=True)
class CostBreakdown:
    provider: str
    tokens_cost: float
    media_cost: float
    storage_cost: float
    gpu_cost: float
    base_cost: float
    total_usd: float
    credits: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "tokens_cost": round(self.tokens_cost, 6),
            "media_cost": round(self.media_cost, 6),
            "storage_cost": round(self.storage_cost, 6),
            "gpu_cost": round(self.gpu_cost, 6),
            "base_cost": round(self.base_cost, 6),
            "total_usd": round(self.total_usd, 6),
            "credits": round(self.credits, 4),
        }


def rates_for(provider: str) -> dict[str, float]:
    key = (provider or "").strip().lower()
    return dict(PROVIDER_RATES.get(key) or PROVIDER_RATES["openai"])


def calculate_cost(
    provider: str,
    *,
    tokens: int = 0,
    images: int = 0,
    video_sec: float = 0.0,
    audio_sec: float = 0.0,
    voice_sec: float = 0.0,
    storage_mb: float = 0.0,
    gpu_sec: float = 0.0,
    requests: int = 1,
) -> CostBreakdown:
    r = rates_for(provider)
    tokens_cost = (max(0, tokens) / 1000.0) * r["token_per_1k"]
    media_cost = (
        max(0, images) * r["image"]
        + max(0.0, video_sec) * r["video_sec"]
        + max(0.0, audio_sec) * r["audio_sec"]
        + max(0.0, voice_sec) * r["voice_sec"]
    )
    storage_cost = max(0.0, storage_mb) * r["storage_mb"]
    gpu_cost = max(0.0, gpu_sec) * r["gpu_sec"]
    base_cost = max(0, requests) * r["request_base"]
    total = tokens_cost + media_cost + storage_cost + gpu_cost + base_cost
    credits = total / CREDIT_USD if CREDIT_USD else 0.0
    return CostBreakdown(
        provider=(provider or "openai").lower(),
        tokens_cost=tokens_cost,
        media_cost=media_cost,
        storage_cost=storage_cost,
        gpu_cost=gpu_cost,
        base_cost=base_cost,
        total_usd=total,
        credits=credits,
    )


def estimated_cost_per_1k(provider: str) -> float:
    r = rates_for(provider)
    # Blend token + request base into a comparable unit cost
    return r["token_per_1k"] + (r["request_base"] * 10.0) + (r["image"] * 0.25)
