"""Monitoring snapshots and alerts for Multi GPU fleet."""

from __future__ import annotations

import time
from typing import Any

from app.services.multi_gpu.models import MonitorSnapshot, MultiGpuJob, GpuWorker


def build_monitor_snapshot(
    workers: list[GpuWorker],
    jobs: list[MultiGpuJob],
) -> MonitorSnapshot:
    online = [w for w in workers if w.state == "online"]
    busy = [w for w in workers if w.state == "busy"]
    active = [w for w in workers if w.state in ("online", "busy")]
    avg_load = (
        sum(w.load for w in active) / len(active) if active else 0.0
    )

    sku_util: dict[str, float] = {}
    by_sku: dict[str, list[GpuWorker]] = {}
    for w in active:
        by_sku.setdefault(w.sku, []).append(w)
    for sku, group in by_sku.items():
        sku_util[sku] = round(sum(w.load for w in group) / len(group), 3)

    queue_depth = sum(1 for j in jobs if j.state in ("queued", "retrying"))
    running = sum(1 for j in jobs if j.state in ("running", "assigned"))
    failed = sum(1 for j in jobs if j.state == "failed")
    retrying = sum(1 for j in jobs if j.state == "retrying")

    alerts: list[str] = []
    if not active:
        alerts.append("CRITICAL: no online GPU workers")
    if avg_load >= 0.9:
        alerts.append("HIGH_LOAD: fleet average load >= 0.9")
    if queue_depth >= max(8, len(active) * 3):
        alerts.append(f"QUEUE_BACKUP: depth={queue_depth}")
    if failed >= 3:
        alerts.append(f"FAILURES: {failed} jobs failed")
    stale = [
        w.worker_id
        for w in workers
        if w.state in ("online", "busy") and time.time() - w.last_heartbeat_sec > 120
    ]
    if stale:
        alerts.append(f"STALE_HEARTBEAT: {', '.join(stale[:4])}")
    for sku, util in sku_util.items():
        if util >= 0.95:
            alerts.append(f"SKU_SATURATED: {sku} util={util}")

    return MonitorSnapshot(
        ts_sec=round(time.time(), 3),
        workers_online=len(online),
        workers_busy=len(busy),
        queue_depth=queue_depth,
        running_jobs=running,
        failed_jobs=failed,
        retrying_jobs=retrying,
        avg_load=round(avg_load, 3),
        sku_utilization=sku_util,
        alerts=alerts,
    )


def monitoring_dict(snapshot: MonitorSnapshot) -> dict[str, Any]:
    return snapshot.to_dict()
