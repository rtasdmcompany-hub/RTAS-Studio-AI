"""Unified Workflow Automation & Pipeline Engine facade."""

from __future__ import annotations

from typing import Any

from app.services.workflow_pipeline import observability, scheduler, store, templates, workflow_engine
from app.services.workflow_pipeline.version import ENGINE_LABEL, ENGINE_NAME, ENGINE_VERSION


class WorkflowPipelineEngine:
    def create(self, **kwargs: Any) -> dict[str, Any]:
        result = workflow_engine.create_workflow(**kwargs)
        return {"engine": ENGINE_NAME, "version": ENGINE_VERSION, **result}

    def start(self, *, user_id: str, workflow_id: str) -> dict[str, Any]:
        result = workflow_engine.start_workflow(user_id=user_id, workflow_id=workflow_id)
        return {"engine": ENGINE_NAME, "version": ENGINE_VERSION, **result}

    def resume(self, *, user_id: str, workflow_id: str) -> dict[str, Any]:
        result = workflow_engine.resume_workflow(user_id=user_id, workflow_id=workflow_id)
        return {"engine": ENGINE_NAME, "version": ENGINE_VERSION, **result}

    def cancel(self, *, user_id: str, workflow_id: str) -> dict[str, Any]:
        result = workflow_engine.cancel_workflow(user_id=user_id, workflow_id=workflow_id)
        return {"engine": ENGINE_NAME, "version": ENGINE_VERSION, **result}

    def get(self, workflow_id: str, *, user_id: str | None = None) -> dict[str, Any]:
        result = workflow_engine.get_workflow(workflow_id, user_id=user_id)
        return {"engine": ENGINE_NAME, "version": ENGINE_VERSION, "label": ENGINE_LABEL, **result}

    def history(self, *, user_id: str | None = None, limit: int = 50) -> dict[str, Any]:
        result = workflow_engine.workflow_history(user_id=user_id, limit=limit)
        return {"engine": ENGINE_NAME, "version": ENGINE_VERSION, **result}

    def pipeline_status(self) -> dict[str, Any]:
        result = workflow_engine.pipeline_status()
        return {"engine": ENGINE_NAME, "version": ENGINE_VERSION, **result}

    def templates(self) -> dict[str, Any]:
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "templates": templates.list_templates(),
        }

    def observability(self) -> dict[str, Any]:
        return {"ok": True, **observability.metrics()}


_engine: WorkflowPipelineEngine | None = None


def get_workflow_engine() -> WorkflowPipelineEngine:
    global _engine
    if _engine is None:
        _engine = WorkflowPipelineEngine()
    return _engine


def reset_engine() -> None:
    global _engine
    store.clear()
    templates.clear_custom()
    scheduler.reset_scheduler()
    _engine = None
