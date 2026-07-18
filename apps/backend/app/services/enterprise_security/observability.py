"""Security observability metrics."""

from __future__ import annotations

from typing import Any

from app.services.enterprise_security import store
from app.services.enterprise_security.audit import audit_health
from app.services.enterprise_security.secrets import secret_validation_report


def metrics() -> dict[str, Any]:
    audits = store.audits(limit=2000)
    events = store.events(limit=2000)
    access = store.access_logs(limit=2000)

    failed_logins = sum(
        1 for a in audits if a.action == "login" and not a.success
    )
    api_errors = sum(1 for a in access if a.status >= 400)
    unauthorized = sum(
        1
        for a in audits
        if a.action == "unauthorized" or (a.action == "api_call" and not a.success and "unauth" in (a.detail or "").lower())
    )
    unauthorized += sum(1 for e in events if e.event_type == "unauthorized")
    violations = sum(1 for e in events if e.event_type == "security_violation")
    provider_access = sum(1 for a in audits if a.action == "ai_provider_usage")
    secrets = secret_validation_report()

    return {
        "failed_logins": failed_logins,
        "api_errors": api_errors,
        "unauthorized_requests": unauthorized,
        "security_violations": violations,
        "provider_access": provider_access,
        "secret_validation": {
            "healthy": secrets["healthy"],
            "present_count": secrets["present_count"],
            "jwt_secret_configured": secrets["jwt_secret_configured"],
            "source": secrets["source"],
        },
        "audit_health": audit_health(),
    }
