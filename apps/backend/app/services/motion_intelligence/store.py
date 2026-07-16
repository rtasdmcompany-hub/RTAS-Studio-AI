"""In-memory store for Motion Intelligence plans."""

from __future__ import annotations

from app.services.motion_intelligence.models import MotionIntelligencePlan

_JOBS: dict[str, MotionIntelligencePlan] = {}


def put_plan(plan: MotionIntelligencePlan) -> None:
    _JOBS[plan.job_id] = plan


def get_plan(job_id: str) -> MotionIntelligencePlan | None:
    return _JOBS.get(job_id)


def clear() -> None:
    _JOBS.clear()
