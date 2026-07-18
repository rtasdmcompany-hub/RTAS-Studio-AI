"""Performance metrics for memory / knowledge engine."""

from __future__ import annotations

import threading
import time
from typing import Any

_lock = threading.Lock()
_retrieval_times: list[float] = []
_search_scores: list[float] = []
_context_scores: list[float] = []


def record_retrieval(ms: float, *, score: float | None = None) -> None:
    with _lock:
        _retrieval_times.append(ms)
        if len(_retrieval_times) > 2000:
            del _retrieval_times[:500]
        if score is not None:
            _search_scores.append(score)
            if len(_search_scores) > 2000:
                del _search_scores[:500]


def record_context_accuracy(score: float) -> None:
    with _lock:
        _context_scores.append(max(0.0, min(1.0, score)))
        if len(_context_scores) > 2000:
            del _context_scores[:500]


def timed() -> float:
    return time.perf_counter()


def elapsed_ms(start: float) -> float:
    return (time.perf_counter() - start) * 1000.0


def summary(*, memory_count: int, knowledge_count: int, cache_stats: dict) -> dict[str, Any]:
    with _lock:
        avg_ret = sum(_retrieval_times) / len(_retrieval_times) if _retrieval_times else 0.0
        avg_search = sum(_search_scores) / len(_search_scores) if _search_scores else 0.0
        avg_ctx = sum(_context_scores) / len(_context_scores) if _context_scores else 1.0
        # Index health: healthy if we have records and search scores aren't collapsing
        health = 100.0
        if knowledge_count == 0:
            health = 70.0
        elif avg_search < 0.05 and _search_scores:
            health = 60.0
        elif avg_search >= 0.2:
            health = 98.0
        return {
            "retrieval_time_ms": round(avg_ret, 3),
            "memory_size": memory_count,
            "knowledge_size": knowledge_count,
            "cache_hit_rate": cache_stats.get("hit_rate", 100.0),
            "search_accuracy": round(avg_search * 100.0, 2),
            "context_accuracy": round(avg_ctx * 100.0, 2),
            "knowledge_index_health": round(health, 2),
            "samples": {
                "retrievals": len(_retrieval_times),
                "searches": len(_search_scores),
                "contexts": len(_context_scores),
            },
        }


def clear() -> None:
    with _lock:
        _retrieval_times.clear()
        _search_scores.clear()
        _context_scores.clear()
