"""Routing domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

RequestType = Literal[
    "text",
    "chat",
    "image",
    "video",
    "audio",
    "music",
    "voice",
    "vision",
    "translation",
    "code",
]

ALL_REQUEST_TYPES: tuple[RequestType, ...] = (
    "text",
    "chat",
    "image",
    "video",
    "audio",
    "music",
    "voice",
    "vision",
    "translation",
    "code",
)


@dataclass
class ModelEntry:
    model_id: str
    provider_id: str
    request_types: list[RequestType]
    priority: int = 50
    cost_per_1k: float = 0.01
    latency_ms: float = 400.0
    quality_score: float = 0.85
    load: float = 0.2  # 0–1 utilization
    enabled: bool = True
    version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RoutingDecision:
    request_type: RequestType
    primary_provider: str
    primary_model: str
    fallback_chain: list[dict[str, str]]
    strategy: str
    score: float
    cost_score: float
    latency_score: float
    quality_score: float
    load_score: float
    reasons: list[str] = field(default_factory=list)
    confidence: float = 0.9

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RoutingPlan:
    plan_id: str
    prompt: str
    request_type: RequestType
    decision: RoutingDecision
    failover_enabled: bool = True
    load_balanced: bool = True
    analytics_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "prompt": self.prompt,
            "request_type": self.request_type,
            "decision": self.decision.to_dict(),
            "failover_enabled": self.failover_enabled,
            "load_balanced": self.load_balanced,
            "analytics_id": self.analytics_id,
            "selected_provider": self.decision.primary_provider,
            "selected_model": self.decision.primary_model,
            "fallback_chain": list(self.decision.fallback_chain),
        }
