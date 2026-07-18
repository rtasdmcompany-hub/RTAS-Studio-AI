"""Datamodels for memory, context, knowledge, and retrieval."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

MemoryType = Literal[
    "short_term",
    "long_term",
    "project",
    "character",
    "scene",
    "story",
    "user_preferences",
    "production_history",
    "asset_references",
    "ai_decision_history",
    "prompt",
    "conversation",
    "user",
    "asset",
]

KnowledgeKind = Literal[
    "project",
    "character",
    "scene",
    "asset",
    "prompt",
    "template",
    "style",
    "preset",
    "production_report",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


@dataclass
class MemoryRecord:
    memory_id: str
    memory_type: MemoryType
    user_id: str
    project_id: str | None
    title: str
    content: str
    content_encrypted: str
    tags: list[str] = field(default_factory=list)
    character_id: str | None = None
    scene_id: str | None = None
    asset_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    importance: float = 0.5
    expires_at: str | None = None
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self, *, include_content: bool = True) -> dict[str, Any]:
        d = asdict(self)
        if not include_content:
            d.pop("content", None)
            d.pop("content_encrypted", None)
        return d


@dataclass
class ContextRecord:
    context_id: str
    user_id: str
    project_id: str | None
    previous_prompts: list[str] = field(default_factory=list)
    previous_outputs: list[str] = field(default_factory=list)
    story_continuity: dict[str, Any] = field(default_factory=dict)
    character_continuity: dict[str, Any] = field(default_factory=dict)
    scene_continuity: dict[str, Any] = field(default_factory=dict)
    camera_continuity: dict[str, Any] = field(default_factory=dict)
    audio_continuity: dict[str, Any] = field(default_factory=dict)
    environment_continuity: dict[str, Any] = field(default_factory=dict)
    user_workflow: dict[str, Any] = field(default_factory=dict)
    memory_refs: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class KnowledgeRecord:
    knowledge_id: str
    kind: KnowledgeKind
    user_id: str
    project_id: str | None
    title: str
    body: str
    tokens: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TimelineEntry:
    entry_id: str
    user_id: str
    project_id: str | None
    event_type: str
    summary: str
    ref_id: str | None = None
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AuditLogEntry:
    audit_id: str
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    project_id: str | None = None
    detail: str = ""
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RetrievalResult:
    ref_id: str
    source: str
    score: float
    title: str
    snippet: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
