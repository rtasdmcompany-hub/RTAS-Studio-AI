"""Platform stress testing — 50 / 100 / 250 / 500 / 1000 jobs."""

from __future__ import annotations

import time
from typing import Any

from app.services.enterprise_platform.models import StressResult


def _job_state(job) -> str:
    if job is None:
        return "missing"
    if isinstance(job, dict):
        return str(job.get("state") or "")
    return str(getattr(job, "state", ""))


def run_stress(counts: list[int] | None = None) -> dict[str, Any]:
    from app.services import job_orchestration as jo
    from app.services.monitoring_observability import get_monitoring_engine

    sizes = counts or [50, 100, 250, 500, 1000]
    results: list[StressResult] = []
    mon = get_monitoring_engine()

    for n in sizes:
        jo.reset_orchestrator()
        jo.set_max_concurrent(min(32, max(8, n // 20)))
        t0 = time.perf_counter()
        recovery_t0 = None
        ids = []
        provider_switches = 0
        last_provider = None

        for i in range(n):
            priority = ("critical", "high", "normal", "low")[i % 4]
            created = jo.create_job(
                prompt=f"stress {n}/{i}",
                priority=priority,
                metadata={"work_ms": 1},
                auto_process=True,
            )
            ids.append(created["job_id"])
            prov = created.get("provider")
            if last_provider and prov and prov != last_provider:
                provider_switches += 1
            last_provider = prov or last_provider

        # Inject a brief recovery mid-run for larger batches
        if n >= 250:
            recovery_t0 = time.perf_counter()
            mon.simulate_failure("queue")
            mon.recovery({"component": "queue", "actions": ["recover_queue", "reconnect_service"]})
            recovery_ms = (time.perf_counter() - recovery_t0) * 1000.0
        else:
            recovery_ms = 0.0

        done = 0
        failed = 0
        latencies: list[float] = []
        deadline = time.perf_counter() + max(30.0, n * 0.05)
        while time.perf_counter() < deadline and done < n:
            jo.pump_scheduler()
            done = 0
            failed = 0
            latencies = []
            for jid in ids:
                j = jo.get_job(jid)
                state = _job_state(j)
                if state in ("completed", "failed", "cancelled"):
                    done += 1
                    if state == "failed":
                        failed += 1
                    if isinstance(j, dict):
                        m = j.get("metrics") or {}
                        latencies.append(float(m.get("total_time_ms") or m.get("processing_time_ms") or 0))
                    else:
                        metrics = getattr(j, "metrics", None)
                        if metrics:
                            latencies.append(
                                float(
                                    getattr(metrics, "total_time_ms", 0)
                                    or getattr(metrics, "processing_time_ms", 0)
                                    or 0
                                )
                            )
            if done < n:
                time.sleep(0.01)

        elapsed = time.perf_counter() - t0
        completed = done - failed
        avg_lat = sum(latencies) / len(latencies) if latencies else 0.0
        status = jo.jobs_status()
        queue_time = float(status.get("avg_queue_time_ms") or status.get("avg_total_time_ms") or avg_lat)
        # Resource estimates from throughput pressure
        cpu_est = min(95.0, 25.0 + (n / 1000.0) * 50.0)
        mem_est = min(95.0, 30.0 + (n / 1000.0) * 45.0)
        mon.record_request(success=failed == 0, latency_ms=avg_lat or 20.0)

        results.append(
            StressResult(
                job_count=n,
                completed=completed,
                failed=failed,
                elapsed_sec=round(elapsed, 3),
                jobs_per_sec=round((n / elapsed) if elapsed else 0.0, 2),
                avg_latency_ms=round(avg_lat, 2),
                failure_rate=round((failed / n) * 100.0 if n else 0.0, 2),
                queue_time_ms=round(queue_time, 2),
                recovery_time_ms=round(recovery_ms, 2),
                provider_switches=provider_switches,
                cpu_estimate=round(cpu_est, 2),
                memory_estimate=round(mem_est, 2),
            )
        )

    # Pass criteria: each batch completes >= 95% and failure_rate < 5
    all_pass = all(r.completed >= int(r.job_count * 0.95) and r.failure_rate < 5 for r in results)
    return {
        "ok": all_pass,
        "batches": [r.to_dict() for r in results],
        "summary": {
            "total_jobs": sum(r.job_count for r in results),
            "total_completed": sum(r.completed for r in results),
            "avg_jobs_per_sec": round(
                sum(r.jobs_per_sec for r in results) / max(1, len(results)), 2
            ),
            "max_failure_rate": max((r.failure_rate for r in results), default=0.0),
            "passed": all_pass,
        },
    }
