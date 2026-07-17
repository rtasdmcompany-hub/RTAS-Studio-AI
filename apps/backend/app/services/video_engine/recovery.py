"""Error recovery and automatic retry for pipeline stages."""

from __future__ import annotations

from app.services.video_engine.models import PipelineStage, RecoveryPlan

# Stages that can be auto-retried without full replan
_RETRYABLE = {
    "generation",
    "rendering",
    "export",
    "download",
    "camera",
}


def apply_automatic_retry(
    stages: list[PipelineStage],
    *,
    max_attempts: int = 3,
    auto_retry: bool = True,
) -> tuple[list[PipelineStage], RecoveryPlan]:
    recovered: list[str] = []
    pending: list[dict] = []
    total_retries = 0

    if not auto_retry:
        return stages, RecoveryPlan(
            enabled=False,
            auto_retry=False,
            max_attempts=max_attempts,
            recovered_stages=[],
            pending_retries=[],
            strategy="manual",
        )

    for stage in stages:
        if stage.status != "failed":
            continue
        if stage.name not in _RETRYABLE:
            pending.append(
                {
                    "stage": stage.name,
                    "reason": "not_auto_retryable",
                    "errors": stage.errors,
                }
            )
            continue
        if stage.retries >= max_attempts:
            pending.append(
                {
                    "stage": stage.name,
                    "reason": "max_attempts_exceeded",
                    "attempts": stage.retries,
                }
            )
            continue

        # Soft recovery: mark recovered when failure is non-blocking soft miss
        soft = any("missing_" in e for e in stage.errors) and stage.score >= 0.35
        stage.retries += 1
        total_retries += 1
        if soft or stage.name in ("download", "generation"):
            # Recover to pending/recovered for orchestration to re-kick
            stage.status = "recovered"
            stage.errors = []
            stage.notes.append(f"auto-retry #{stage.retries} scheduled")
            stage.score = min(1.0, stage.score + 0.15)
            recovered.append(stage.name)
        else:
            pending.append(
                {
                    "stage": stage.name,
                    "reason": "retry_queued",
                    "attempt": stage.retries,
                    "backoff_ms": 500 * stage.retries,
                }
            )
            stage.status = "pending"
            stage.notes.append(f"auto-retry #{stage.retries} queued")

    return stages, RecoveryPlan(
        enabled=True,
        auto_retry=True,
        max_attempts=max_attempts,
        recovered_stages=recovered,
        pending_retries=pending,
        strategy="stage_level_auto_retry",
    )
