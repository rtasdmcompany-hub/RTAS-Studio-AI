"""Built-in and custom workflow templates."""

from __future__ import annotations

from app.services.workflow_pipeline.models import (
    PRODUCTION_STAGES,
    StageSpec,
    WorkflowTemplate,
    new_id,
)

_CUSTOM: dict[str, WorkflowTemplate] = {}


def _chain(stages: tuple[str, ...] | list[str]) -> list[StageSpec]:
    specs: list[StageSpec] = []
    prev: str | None = None
    for name in stages:
        deps = [prev] if prev else []
        specs.append(StageSpec(name=name, depends_on=deps))
        prev = name
    return specs


def production_pipeline_template() -> WorkflowTemplate:
    return WorkflowTemplate(
        template_id="tpl_production_full",
        name="Full Production Pipeline",
        description="Prompt → Story → … → Export → Download",
        stages=_chain(PRODUCTION_STAGES),
        builtin=True,
    )


def story_to_export_template() -> WorkflowTemplate:
    stages = (
        "story",
        "director",
        "scene",
        "character",
        "motion",
        "camera",
        "environment",
        "audio",
        "video",
        "export",
    )
    return WorkflowTemplate(
        template_id="tpl_story_export",
        name="Story to Export",
        description="Start from story through export",
        stages=_chain(stages),
        builtin=True,
    )


def builtin_templates() -> list[WorkflowTemplate]:
    return [production_pipeline_template(), story_to_export_template()]


def get_template(template_id: str | None) -> WorkflowTemplate:
    if not template_id or template_id == "default":
        return production_pipeline_template()
    for t in builtin_templates():
        if t.template_id == template_id or t.name == template_id:
            return t
    if template_id in _CUSTOM:
        return _CUSTOM[template_id]
    raise ValueError(f"unknown workflow template: {template_id}")


def register_custom_template(
    name: str,
    stages: list[str],
    *,
    description: str = "Custom workflow",
) -> WorkflowTemplate:
    if not stages:
        raise ValueError("custom workflow requires at least one stage")
    tpl = WorkflowTemplate(
        template_id=new_id("tpl"),
        name=name or "custom",
        description=description,
        stages=_chain(stages),
        builtin=False,
    )
    _CUSTOM[tpl.template_id] = tpl
    return tpl


def list_templates() -> list[dict]:
    return [t.to_dict() for t in builtin_templates()] + [t.to_dict() for t in _CUSTOM.values()]


def clear_custom() -> None:
    _CUSTOM.clear()
