"""Routing analytics store."""

from __future__ import annotations

import hashlib
import threading
import time
from collections import OrderedDict
from typing import Any

_lock = threading.Lock()
_events: OrderedDict[str, dict[str, Any]] = OrderedDict()
_MAX = 2000


def record_routing(
    *,
    request_type: str,
    provider: str,
    model: str,
    score: float,
    strategy: str,
    prompt: str = "",
) -> str:
    digest = hashlib.sha1(f"{time.time_ns()}|{provider}|{model}".encode()).hexdigest()
    event_id = f"route_{digest[:12]}"
    entry = {
        "analytics_id": event_id,
        "request_type": request_type,
        "provider": provider,
        "model": model,
        "score": score,
        "strategy": strategy,
        "prompt_len": len(prompt or ""),
        "ts": time.time(),
    }
    with _lock:
        _events[event_id] = entry
        while len(_events) > _MAX:
            _events.popitem(last=False)
    return event_id


def summary(limit: int = 100) -> dict[str, Any]:
    with _lock:
        items = list(_events.values())[-max(1, min(500, limit)) :]
    by_type: dict[str, int] = {}
    by_provider: dict[str, int] = {}
    scores: list[float] = []
    for e in items:
        by_type[e["request_type"]] = by_type.get(e["request_type"], 0) + 1
        by_provider[e["provider"]] = by_provider.get(e["provider"], 0) + 1
        scores.append(float(e["score"]))
    return {
        "events": list(reversed(items)),
        "count": len(items),
        "by_request_type": by_type,
        "by_provider": by_provider,
        "avg_score": round(sum(scores) / len(scores), 4) if scores else 0.0,
    }


def clear() -> None:
    with _lock:
        _events.clear()
