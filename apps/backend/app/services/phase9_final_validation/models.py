"""Validation run / quality report domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def new_id(prefix: str = "p9v_") -> str:
    return f"{prefix}{uuid4()}"


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ValidationRunRecord:
    id: str
    kind: str  # integration | regression | e2e | load | security | quality
    passed: bool = True
    score: float = 100.0
    details: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "passed": self.passed,
            "score": self.score,
            "details": dict(self.details),
            "createdAt": _iso(self.created_at),
        }


@dataclass
class LoadResultRecord:
    id: str
    users: int
    elapsed_sec: float
    ops_per_sec: float
    avg_latency_ms: float
    failures: int
    recovered: int
    failure_rate_pct: float
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "users": self.users,
            "elapsedSec": round(self.elapsed_sec, 4),
            "opsPerSec": round(self.ops_per_sec, 2),
            "avgLatencyMs": round(self.avg_latency_ms, 3),
            "failures": self.failures,
            "recovered": self.recovered,
            "failureRatePct": round(self.failure_rate_pct, 4),
            "createdAt": _iso(self.created_at),
        }
