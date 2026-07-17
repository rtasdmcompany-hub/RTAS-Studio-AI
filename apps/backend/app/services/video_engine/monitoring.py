"""Pipeline monitoring and alerts."""

from __future__ import annotations

from app.services.video_engine.models import MonitorSnapshot, PipelineStage, ValidationResult


def build_monitoring(
    stages: list[PipelineStage],
    validation: ValidationResult,
    *,
    retry_total: int = 0,
) -> MonitorSnapshot:
    failed = [s for s in stages if s.status == "failed"]
    recovered = [s for s in stages if s.status == "recovered"]
    stage_health = {
        s.name: (
            "ok"
            if s.status in ("passed", "recovered")
            else ("warn" if s.status == "pending" else "error")
        )
        for s in stages
    }
    error_rate = round(len(failed) / max(1, len(stages)), 3)
    retry_rate = round(retry_total / max(1, len(stages)), 3)

    alerts: list[str] = []
    alerts.extend(validation.blockers[:6])
    for s in failed:
        alerts.append(f"STAGE_FAIL:{s.name}")
    if error_rate >= 0.34:
        alerts.append(f"HIGH_ERROR_RATE:{error_rate}")
    if retry_rate >= 0.5:
        alerts.append(f"HIGH_RETRY_RATE:{retry_rate}")

    if validation.passed and not failed:
        status = "healthy"
        healthy = True
    elif validation.passed and recovered:
        status = "degraded_recovered"
        healthy = True
    elif failed:
        status = "unhealthy"
        healthy = False
    else:
        status = "degraded"
        healthy = False

    return MonitorSnapshot(
        healthy=healthy,
        pipeline_status=status,
        active_alerts=alerts[:12],
        stage_health=stage_health,
        error_rate=error_rate,
        retry_rate=retry_rate,
    )
