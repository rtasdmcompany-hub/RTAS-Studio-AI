"""In-memory store for Physics plans."""

from __future__ import annotations

from app.services.physics.models import PhysicsPlan

_JOBS: dict[str, PhysicsPlan] = {}


def put_plan(plan: PhysicsPlan) -> None:
    _JOBS[plan.job_id] = plan


def get_plan(job_id: str) -> PhysicsPlan | None:
    return _JOBS.get(job_id)


def clear() -> None:
    _JOBS.clear()
