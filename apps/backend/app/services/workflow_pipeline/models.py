"""Datamodels for workflows, pipelines, stages, and automation logs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

WorkflowStatus = Literal[
    "draft",
    "queued",
    "running",
    "paused",
    "waiting",
    "completed",
    "failed",
    "cancelled",
    "recovering",
]

StageStatus = Literal[
    "pending",
    "ready",
    "running",
    "completed",
    "failed",
    "skipped",
    "retrying",
]

TERMINAL_WORKFLOW = frozenset({"completed", "failed", "cancelled"})

PRODUCTION_STAGES: tuple[str, ...] = (
    "prompt",
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
    "download",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


@dataclass
class StageSpec:
    name: str
    depends_on: list[str] = field(default_factory=list)
    timeout_sec: float = 30.0
    max_retries: int = 3
    optional: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StageRuntime:
    name: str
    status: StageStatus = "pending"
    retry_count: int = 0
    started_at: str | None = None
    completed_at: str | None = None
    processing_time_ms: float = 0.0
    error: str | None = None
    output: dict[str, Any] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WorkflowTemplate:
    template_id: str
    name: str
    description: str
    stages: list[StageSpec]
    builtin: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "stages": [s.to_dict() for s in self.stages],
            "builtin": self.builtin,
        }


@dataclass
class WorkflowJob:
    workflow_id: str
    user_id: str
    project_id: str | None
    name: str
    template_id: str
    status: WorkflowStatus
    prompt: str
    stages: list[StageRuntime]
    active_stage: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    auto_trigger: bool = True
    notifications: list[str] = field(default_factory=list)
    logs: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    started_at: str | None = None
    completed_at: str | None = None
    processing_time_ms: float = 0.0
    _t0: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("_t0", None)
        return d


@dataclass
class AutomationLog:
    log_id: str
    workflow_id: str
    action: str
    detail: str
    stage: str | None = None
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AuditEntry:
    audit_id: str
    user_id: str
    action: str
    workflow_id: str
    detail: str = ""
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
