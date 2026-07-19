"""Operational runbooks for incident response (embedded ops docs)."""

from __future__ import annotations

from typing import Any

RUNBOOKS: dict[str, dict[str, Any]] = {
    "api_failure": {
        "title": "API / FastAPI Failure",
        "severity": ["Check /api/health/ping", "Check /api/ready", "Review Vercel deployment"],
        "escalation": "Redeploy API; verify AI_BACKEND_SECRET and CORS",
        "recovery": "POST /api/system/recovery with reconnect_service",
    },
    "database_failure": {
        "title": "Database Failure",
        "severity": ["Confirm DATABASE_URL", "prisma migrate status", "provider status page"],
        "escalation": "Point-in-time restore + prisma migrate deploy",
        "recovery": "Clear forced failure; reconnect_service(database)",
    },
    "queue_failure": {
        "title": "Queue Failure",
        "severity": ["GET /api/jobs/status", "Inspect DLQ depth", "Worker online count"],
        "escalation": "recover_workers + DLQ requeue",
        "recovery": "POST /api/jobs/recover-workers; system recovery recover_queue",
    },
    "worker_failure": {
        "title": "Worker Failure",
        "severity": ["Failed/offline workers in monitoring store", "Job orchestration pool"],
        "escalation": "restart_failed_workers + scale concurrent workers",
        "recovery": "self_healing.restart_failed_workers()",
    },
    "ai_provider_failure": {
        "title": "AI Provider Failure",
        "severity": ["Provider health states", "FAL/Replicate keys", "failover chain"],
        "escalation": "Switch provider via invoke_with_failover",
        "recovery": "automatic_failover(ai_providers)",
    },
    "billing_failure": {
        "title": "Billing Failure",
        "severity": ["Paddle/PayPal webhooks", "idempotency store", "payment_failure alerts"],
        "escalation": "Verify webhook secrets; replay failed events",
        "recovery": "Clear paddle forced failure; review billing audit logs",
    },
    "storage_failure": {
        "title": "Storage Failure",
        "severity": ["ensure_dirs", "blob/S3 credentials", "upload path sanitization"],
        "escalation": "Remount object storage; rotate credentials",
        "recovery": "ensure_dirs + clear storage forced failure",
    },
    "auth_failure": {
        "title": "Authentication Failure",
        "severity": ["NextAuth sessions", "backend secret mismatch", "JWT fail-closed"],
        "escalation": "Rotate AI_BACKEND_SECRET; verify NEXTAUTH_SECRET",
        "recovery": "Clear authentication forced failure; review auth audit",
    },
    "security_event": {
        "title": "Security Event",
        "severity": ["/api/security/events", "content moderation log", "SSRF/upload rejects"],
        "escalation": "Acknowledge incident; freeze suspect keys if needed",
        "recovery": "Mitigate incident; update security status to resolved",
    },
}


def list_runbooks() -> dict[str, Any]:
    return {
        "ok": True,
        "count": len(RUNBOOKS),
        "runbooks": [
            {"id": key, **value} for key, value in RUNBOOKS.items()
        ],
    }


def get_runbook(runbook_id: str) -> dict[str, Any] | None:
    item = RUNBOOKS.get(runbook_id)
    if not item:
        return None
    return {"id": runbook_id, **item}
