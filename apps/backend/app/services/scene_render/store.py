"""In-memory store for Scene Render plans."""

from __future__ import annotations

from app.services.scene_render.models import SceneRenderPlan

_JOBS: dict[str, SceneRenderPlan] = {}


def put_plan(plan: SceneRenderPlan) -> None:
    _JOBS[plan.job_id] = plan


def get_plan(job_id: str) -> SceneRenderPlan | None:
    return _JOBS.get(job_id)


def clear() -> None:
    _JOBS.clear()
