"""In-memory store for Multi GPU plans."""

from __future__ import annotations

from app.services.multi_gpu.models import MultiGpuPlan

_JOBS: dict[str, MultiGpuPlan] = {}


def put_plan(plan: MultiGpuPlan) -> None:
    _JOBS[plan.job_id] = plan


def get_plan(job_id: str) -> MultiGpuPlan | None:
    return _JOBS.get(job_id)


def clear() -> None:
    _JOBS.clear()
