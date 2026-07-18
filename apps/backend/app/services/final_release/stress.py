"""Phase 5 final release stress harness — 50 / 100 / 250 / 500 jobs."""

from __future__ import annotations

import time
import tracemalloc
from typing import Any

from app.services.director_intelligence.engine import generate_director
from app.services.director_intelligence.queue import director_queue
from app.services.final_release.version import QUALITY_THRESHOLD, STRESS_BATCHES


def _perf_snapshot() -> dict[str, Any]:
    mem_current = mem_peak = 0.0
    if tracemalloc.is_tracing():
        current, peak = tracemalloc.get_traced_memory()
        mem_current = round(current / (1024 * 1024), 3)
        mem_peak = round(peak / (1024 * 1024), 3)
    return {
        "memory_mb": mem_current,
        "memory_peak_mb": mem_peak,
        "cpu": "process",  # measured via elapsed wall time
        "gpu": "simulation",
        "queue": director_queue.status(),
    }


def run_stress_batch(job_count: int, *, format_type: str = "shorts") -> dict[str, Any]:
    if job_count < 1:
        raise ValueError("job_count must be >= 1")
    started_trace = False
    if not tracemalloc.is_tracing():
        tracemalloc.start()
        started_trace = True
    t0 = time.perf_counter()
    successes = 0
    failures = 0
    retries = 0
    recovered = 0
    times: list[float] = []
    accuracies: list[float] = []
    try:
        for i in range(job_count):
            jt0 = time.perf_counter()
            try:
                result = generate_director(
                    prompt=f"Phase5 stress cinematic job {i} format {format_type}",
                    project_id=f"stress_p5_{format_type}_{i % 17}",
                    format_type=format_type,
                )
                if result.get("state") == "completed":
                    successes += 1
                    accuracies.append(float(result.get("accuracy_score") or 0))
                else:
                    failures += 1
                    # retry once
                    retries += 1
                    retry = generate_director(job_id=result.get("job_id"))
                    if retry.get("state") == "completed":
                        recovered += 1
                        successes += 1
                        failures -= 1
                        accuracies.append(float(retry.get("accuracy_score") or 0))
            except Exception:
                failures += 1
                retries += 1
            times.append((time.perf_counter() - jt0) * 1000.0)
    finally:
        elapsed = time.perf_counter() - t0
        snap = _perf_snapshot()
        if started_trace:
            tracemalloc.stop()

    avg_ms = round(sum(times) / len(times), 3) if times else 0.0
    p95 = round(sorted(times)[int(0.95 * (len(times) - 1))], 3) if times else 0.0
    min_acc = min(accuracies) if accuracies else 0.0
    return {
        "job_count": job_count,
        "successes": successes,
        "failures": failures,
        "retry_count": retries,
        "retry_success": recovered,
        "failure_recovery_rate": round(100.0 * recovered / max(1, retries), 2) if retries else 100.0,
        "elapsed_sec": round(elapsed, 3),
        "avg_generation_ms": avg_ms,
        "p95_generation_ms": p95,
        "jobs_per_sec": round(job_count / elapsed, 2) if elapsed > 0 else 0.0,
        "min_accuracy": round(min_acc, 2),
        "avg_accuracy": round(sum(accuracies) / len(accuracies), 2) if accuracies else 0.0,
        "accuracy_pass": min_acc >= QUALITY_THRESHOLD if accuracies else False,
        "passed": failures == 0 and (min_acc >= QUALITY_THRESHOLD if accuracies else False),
        **snap,
    }


def run_all_stress_batches(
    batches: tuple[int, ...] = STRESS_BATCHES,
    *,
    max_jobs: int | None = None,
) -> dict[str, Any]:
    """Run stress batches. max_jobs caps each batch for CI (None = full)."""
    results = []
    for n in batches:
        count = min(n, max_jobs) if max_jobs else n
        batch = run_stress_batch(count)
        batch["requested"] = n
        batch["executed"] = count
        results.append(batch)
    all_pass = all(r["passed"] for r in results)
    return {
        "batches": results,
        "all_passed": all_pass,
        "requested_batches": list(batches),
    }
