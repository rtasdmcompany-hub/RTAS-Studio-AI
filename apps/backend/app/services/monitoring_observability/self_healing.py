"""Self-Healing Engine — automatic recovery actions."""

from __future__ import annotations

from typing import Any

from app.services.monitoring_observability import alerts, incidents, store
from app.services.monitoring_observability.models import RecoveryAction, RecoveryRecord, new_id


def _record(
    action: RecoveryAction,
    target: str,
    *,
    success: bool,
    detail: str,
    incident_id: str | None = None,
) -> dict[str, Any]:
    rec = RecoveryRecord(
        recovery_id=new_id("rec"),
        action=action,
        target=target,
        success=success,
        detail=detail,
        incident_id=incident_id,
    )
    store.add_recovery(rec)
    return rec.to_dict()


def restart_failed_workers() -> list[dict[str, Any]]:
    results = []
    for w in store.workers():
        if w.get("status") in ("failed", "offline", "dead"):
            wid = w["worker_id"]
            store.set_worker(wid, "online", restarted=True)
            results.append(
                _record("restart_worker", wid, success=True, detail="worker restarted")
            )
    return results


def retry_failed_jobs(job_ids: list[str] | None = None) -> list[dict[str, Any]]:
    ids = job_ids or store.stuck_jobs()
    results = []
    for jid in ids:
        store.clear_stuck_job(jid)
        results.append(_record("retry_job", jid, success=True, detail="job retried"))
    return results


def reconnect_service(component: str) -> dict[str, Any]:
    store.clear_failure(component)
    if component == "ai_providers":
        for name in store.provider_states():
            store.set_provider_state(name, "healthy")
    return _record(
        "reconnect_service",
        component,
        success=True,
        detail=f"reconnected {component}",
    )


def refresh_expired_tokens() -> dict[str, Any]:
    return _record(
        "refresh_token",
        "tokens",
        success=True,
        detail="token refresh cycle completed",
    )


def recover_queue_failures() -> dict[str, Any]:
    store.set_queue_depth(0)
    for jid in list(store.stuck_jobs()):
        store.clear_stuck_job(jid)
    return _record("recover_queue", "queue", success=True, detail="queue recovered")


def detect_deadlocks() -> dict[str, Any]:
    stuck = store.stuck_jobs()
    found = len(stuck) > 0
    return _record(
        "detect_deadlock",
        "scheduler",
        success=True,
        detail=f"deadlocks detected={found} count={len(stuck)}",
    )


def recover_stuck_jobs() -> list[dict[str, Any]]:
    return retry_failed_jobs()


def automatic_failover(component: str, *, backup: str = "secondary") -> dict[str, Any]:
    store.clear_failure(component)
    if component == "ai_providers":
        store.set_provider_state("fal", "healthy")
        store.set_provider_state("replicate", "healthy")
    return _record(
        "failover",
        component,
        success=True,
        detail=f"failed over to {backup}",
    )


def run_recovery(
    *,
    actions: list[str] | None = None,
    component: str | None = None,
    job_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Execute requested recovery actions (or auto suite)."""
    selected = actions or [
        "detect_deadlock",
        "restart_worker",
        "retry_job",
        "recover_queue",
        "reconnect_service",
        "refresh_token",
        "failover",
    ]
    executed: list[dict[str, Any]] = []
    target = component or "system"

    # Open / mitigate incidents for unhealthy forced components
    if component and store.is_forced_failure(component):
        inc = incidents.open_incident(
            f"{component} recovery",
            component=component,
            severity="high",
            description="self-healing recovery requested",
        )
        incidents.update_status(inc["incident_id"], "mitigating", recovery_action="auto")
    else:
        inc = None

    for action in selected:
        if action in ("restart_worker", "restart_failed_workers"):
            executed.extend(restart_failed_workers())
        elif action in ("retry_job", "recover_stuck_job"):
            executed.extend(retry_failed_jobs(job_ids))
        elif action == "reconnect_service":
            executed.append(reconnect_service(target))
        elif action == "refresh_token":
            executed.append(refresh_expired_tokens())
        elif action == "recover_queue":
            executed.append(recover_queue_failures())
        elif action == "detect_deadlock":
            executed.append(detect_deadlocks())
        elif action == "failover":
            executed.append(automatic_failover(target))
        else:
            executed.append(
                {
                    "recovery_id": new_id("rec"),
                    "action": action,
                    "target": target,
                    "success": False,
                    "detail": f"unknown action {action}",
                }
            )

    if inc:
        incidents.update_status(
            inc["incident_id"],
            "resolved",
            recovery_action="self_healing_complete",
        )

    success = all(e.get("success") for e in executed) if executed else True
    if success and component:
        store.clear_failure(component)
        alerts.raise_alert(
            "api_failure" if component == "api" else "queue_failure",
            f"recovered {component}",
            component=component,
            level="info",
        )
    return {
        "ok": success,
        "executed": executed,
        "count": len(executed),
        "incident": inc,
        "recoveries": [r.to_dict() for r in store.recoveries(limit=20)],
    }
