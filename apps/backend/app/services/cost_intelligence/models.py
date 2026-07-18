"""Datamodels for cost intelligence, analytics, budgets, and rankings."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

UsageKind = Literal[
    "request",
    "tokens",
    "images",
    "videos",
    "audio",
    "voice",
    "storage",
    "gpu_time",
]
ReportPeriod = Literal["daily", "monthly", "project", "team"]
OptimizeMode = Literal["cost", "balanced", "quality", "latency"]

PROVIDER_CATALOG: tuple[str, ...] = (
    "openai",
    "gemini",
    "claude",
    "stability",
    "elevenlabs",
    "runpod",
    "fal",
    "replicate",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


@dataclass
class UsageEvent:
    event_id: str
    provider: str
    kind: UsageKind
    quantity: float
    cost_usd: float
    credits: float = 0.0
    tokens: int = 0
    latency_ms: float = 0.0
    success: bool = True
    project_id: str | None = None
    team_id: str | None = None
    model: str | None = None
    created_at: str = field(default_factory=_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProviderUsageTotals:
    provider: str
    requests: int = 0
    tokens: int = 0
    images: int = 0
    videos: int = 0
    audio: int = 0
    voice: int = 0
    storage_mb: float = 0.0
    gpu_time_sec: float = 0.0
    processing_cost_usd: float = 0.0
    credits: float = 0.0
    successes: int = 0
    failures: int = 0
    total_latency_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        avg_latency = (
            self.total_latency_ms / self.requests if self.requests else 0.0
        )
        success_rate = (
            (self.successes / self.requests) * 100.0 if self.requests else 100.0
        )
        failure_rate = (
            (self.failures / self.requests) * 100.0 if self.requests else 0.0
        )
        return {
            "provider": self.provider,
            "requests": self.requests,
            "tokens": self.tokens,
            "images": self.images,
            "videos": self.videos,
            "audio": self.audio,
            "voice": self.voice,
            "storage": self.storage_mb,
            "gpu_time": self.gpu_time_sec,
            "processing_cost": round(self.processing_cost_usd, 6),
            "credits": round(self.credits, 4),
            "avg_response_time_ms": round(avg_latency, 2),
            "success_rate": round(success_rate, 2),
            "failure_rate": round(failure_rate, 2),
            "cost_per_request": round(
                self.processing_cost_usd / self.requests if self.requests else 0.0,
                6,
            ),
        }


@dataclass
class BudgetProfile:
    budget_id: str
    name: str
    daily_limit_usd: float
    monthly_limit_usd: float
    project_id: str | None = None
    team_id: str | None = None
    spent_daily_usd: float = 0.0
    spent_monthly_usd: float = 0.0
    alert_threshold: float = 0.8
    active: bool = True
    created_at: str = field(default_factory=_now_iso)

    def remaining_daily(self) -> float:
        return max(0.0, self.daily_limit_usd - self.spent_daily_usd)

    def remaining_monthly(self) -> float:
        return max(0.0, self.monthly_limit_usd - self.spent_monthly_usd)

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "remaining_daily_usd": round(self.remaining_daily(), 6),
            "remaining_monthly_usd": round(self.remaining_monthly(), 6),
            "daily_utilization": round(
                self.spent_daily_usd / self.daily_limit_usd
                if self.daily_limit_usd
                else 0.0,
                4,
            ),
            "monthly_utilization": round(
                self.spent_monthly_usd / self.monthly_limit_usd
                if self.monthly_limit_usd
                else 0.0,
                4,
            ),
        }


@dataclass
class ProviderRank:
    provider: str
    rank: int
    score: float
    cost_score: float
    speed_score: float
    availability_score: float
    quality_score: float
    reliability_score: float
    success_rate: float
    error_rate: float
    estimated_cost_per_1k: float
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OptimizationDecision:
    decision_id: str
    mode: OptimizeMode
    selected_provider: str
    selected_model: str | None
    estimated_cost_usd: float
    estimated_latency_ms: float
    quality_score: float
    savings_usd: float
    alternatives: list[dict[str, Any]]
    ranking: list[dict[str, Any]]
    reason: str
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class UsageReport:
    report_id: str
    period: ReportPeriod
    scope_id: str | None
    total_cost_usd: float
    total_credits: float
    total_requests: int
    by_provider: list[dict[str, Any]]
    generated_at: str = field(default_factory=_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
