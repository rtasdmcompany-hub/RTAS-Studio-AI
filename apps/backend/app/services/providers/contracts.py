"""Extended Multi-AI provider contracts (cost, ETA, health, retry)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class CostEstimate:
    provider: str
    currency: str
    estimated_usd: float
    cost_per_second_usd: float
    duration_seconds: int
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ETAEstimate:
    provider: str
    eta_seconds: int
    queue_depth: int = 0
    confidence: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HealthReport:
    provider: str
    healthy: bool
    configured: bool
    latency_ms: float | None = None
    message: str = ""
    checked_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RetryPlan:
    provider: str
    attempt: int
    max_attempts: int
    backoff_seconds: float
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProviderCapability:
    provider: str
    display_name: str
    strengths: list[str] = field(default_factory=list)
    max_duration_seconds: int = 10
    supports_i2v: bool = True
    supports_t2v: bool = True
    fal_model: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
