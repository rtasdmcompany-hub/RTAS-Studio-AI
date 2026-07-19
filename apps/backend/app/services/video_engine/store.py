"""In-memory store for Video Engine plans with bounded eviction."""

from __future__ import annotations

from collections import OrderedDict

from app.services.video_engine.models import VideoEnginePlan

# Cap retained plans to avoid unbounded memory growth under load.
MAX_PLANS = 1000
_JOBS: OrderedDict[str, VideoEnginePlan] = OrderedDict()


def put_plan(plan: VideoEnginePlan) -> None:
    if plan.job_id in _JOBS:
        _JOBS.move_to_end(plan.job_id)
        _JOBS[plan.job_id] = plan
        return
    _JOBS[plan.job_id] = plan
    while len(_JOBS) > MAX_PLANS:
        _JOBS.popitem(last=False)


def get_plan(job_id: str) -> VideoEnginePlan | None:
    plan = _JOBS.get(job_id)
    if plan is not None:
        _JOBS.move_to_end(job_id)
    return plan


def clear() -> None:
    _JOBS.clear()


def size() -> int:
    return len(_JOBS)
