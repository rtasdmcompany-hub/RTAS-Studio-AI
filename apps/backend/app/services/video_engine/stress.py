"""Lightweight stress testing harness for the video engine planner."""

from __future__ import annotations

import time
from typing import Any, Callable

from app.services.video_engine.models import StressTestResult


def run_stress_test(
    build_fn: Callable[..., Any],
    *,
    iterations: int = 5,
    kwargs: dict[str, Any] | None = None,
) -> StressTestResult:
    """
    Run the planner repeatedly to verify stability under load.
    Does not hit external GPUs — pure planning path.
    """
    iters = max(1, min(int(iterations), 25))
    args = dict(kwargs or {})
    # Avoid nested stress during stress
    args["run_stress"] = False
    args.setdefault("auto_retry", True)

    times: list[float] = []
    failures = 0
    notes: list[str] = []

    for i in range(iters):
        t0 = time.perf_counter()
        try:
            plan = build_fn(**args)
            elapsed = (time.perf_counter() - t0) * 1000
            times.append(elapsed)
            if hasattr(plan, "production_ready") and not plan.validation.passed:
                # Not a hard failure — planning succeeded
                notes.append(f"iter{i}: validation soft-fail")
        except Exception as exc:  # noqa: BLE001 — stress must continue
            failures += 1
            times.append((time.perf_counter() - t0) * 1000)
            notes.append(f"iter{i}: {type(exc).__name__}: {exc}")

    success_rate = round((iters - failures) / iters, 3)
    avg = round(sum(times) / max(1, len(times)), 2)
    mx = round(max(times) if times else 0.0, 2)
    if success_rate >= 0.95:
        notes.append("stress OK — planner stable")
    elif success_rate >= 0.8:
        notes.append("stress WARN — intermittent failures")
    else:
        notes.append("stress FAIL — unstable planner")

    return StressTestResult(
        ran=True,
        iterations=iters,
        success_rate=success_rate,
        avg_ms=avg,
        max_ms=mx,
        failures=failures,
        notes=notes[:12],
    )
