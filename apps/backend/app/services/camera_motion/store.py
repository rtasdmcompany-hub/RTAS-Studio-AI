"""In-memory store for Camera Motion plans."""

from __future__ import annotations

from app.services.camera_motion.models import CameraMotionPlan

_JOBS: dict[str, CameraMotionPlan] = {}


def put_plan(plan: CameraMotionPlan) -> None:
    _JOBS[plan.job_id] = plan


def get_plan(job_id: str) -> CameraMotionPlan | None:
    return _JOBS.get(job_id)


def clear() -> None:
    _JOBS.clear()
