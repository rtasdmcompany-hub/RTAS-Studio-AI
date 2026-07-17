"""In-memory store for Video Engine plans."""

from __future__ import annotations

from app.services.video_engine.models import VideoEnginePlan

_JOBS: dict[str, VideoEnginePlan] = {}


def put_plan(plan: VideoEnginePlan) -> None:
    _JOBS[plan.job_id] = plan


def get_plan(job_id: str) -> VideoEnginePlan | None:
    return _JOBS.get(job_id)


def clear() -> None:
    _JOBS.clear()
