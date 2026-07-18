"""Cost / latency / quality / load scoring for routing."""

from __future__ import annotations

from app.services.model_routing.models import ModelEntry


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


def cost_score(entry: ModelEntry, *, prefer_cheap: bool = True) -> float:
    # Lower cost → higher score when prefer_cheap
    # Normalize roughly against $0.05/1k as expensive
    raw = 1.0 - _clamp01(entry.cost_per_1k / 0.05)
    return raw if prefer_cheap else (1.0 - raw)


def latency_score(entry: ModelEntry) -> float:
    # Lower latency → higher score (3s as slow baseline)
    return 1.0 - _clamp01(entry.latency_ms / 3000.0)


def quality_score(entry: ModelEntry) -> float:
    return _clamp01(entry.quality_score)


def load_score(entry: ModelEntry) -> float:
    # Lower load → higher score (load balancing)
    return 1.0 - _clamp01(entry.load)


def composite_score(
    entry: ModelEntry,
    *,
    weights: dict[str, float] | None = None,
    prefer_cheap: bool = True,
) -> dict[str, float]:
    w = {
        "cost": 0.2,
        "latency": 0.25,
        "quality": 0.35,
        "load": 0.2,
        **(weights or {}),
    }
    total_w = sum(w.values()) or 1.0
    c = cost_score(entry, prefer_cheap=prefer_cheap)
    l = latency_score(entry)
    q = quality_score(entry)
    ld = load_score(entry)
    # Model priority bonus (lower priority number is better)
    priority_bonus = max(0.0, (100 - entry.priority) / 100.0) * 0.05
    overall = (
        c * w["cost"] + l * w["latency"] + q * w["quality"] + ld * w["load"]
    ) / total_w + priority_bonus
    return {
        "cost_score": round(c, 4),
        "latency_score": round(l, 4),
        "quality_score": round(q, 4),
        "load_score": round(ld, 4),
        "overall": round(_clamp01(overall), 4),
    }
