"""Director / production plan domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

DirectorJobState = Literal[
    "queued",
    "preparing",
    "story_analysis",
    "production_planning",
    "scene_directing",
    "completed",
    "failed",
    "cancelled",
    "retrying",
]

FILM_BEATS = (
    "intro",
    "hook",
    "story_build",
    "conflict",
    "climax",
    "resolution",
    "outro",
    "credits",
)


@dataclass
class StoryAnalysis:
    genre: str
    format_type: str
    target_audience: str
    emotional_journey: list[str]
    character_relationships: list[str]
    scene_importance: dict[str, float]
    visual_complexity: float
    audio_complexity: float
    estimated_runtime_sec: float
    confidence: float
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ShotPlan:
    shot_id: str
    scene_id: str
    order: int
    camera_angle: str
    duration_sec: float
    character_blocking: list[str]
    dialogue_timing: dict[str, Any]
    emotion: str
    transition: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ScenePlan:
    scene_id: str
    beat: str
    order: int
    title: str
    environment: str
    characters: list[str]
    emotion_flow: str
    music_cue: str
    duration_sec: float
    shots: list[ShotPlan] = field(default_factory=list)
    importance: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "beat": self.beat,
            "order": self.order,
            "title": self.title,
            "environment": self.environment,
            "characters": list(self.characters),
            "emotion_flow": self.emotion_flow,
            "music_cue": self.music_cue,
            "duration_sec": self.duration_sec,
            "importance": self.importance,
            "shots": [s.to_dict() for s in self.shots],
        }


@dataclass
class ProductionPlan:
    plan_id: str
    project_id: str
    format_type: str
    story_structure: list[str]
    scenes: list[ScenePlan]
    character_assignments: dict[str, str]
    environment_assignments: dict[str, str]
    camera_plan: dict[str, Any]
    audio_plan: dict[str, Any]
    render_plan: dict[str, Any]
    export_plan: dict[str, Any]
    total_runtime_sec: float
    shot_count: int
    accuracy_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "project_id": self.project_id,
            "format_type": self.format_type,
            "story_structure": list(self.story_structure),
            "scenes": [s.to_dict() for s in self.scenes],
            "scene_list": [
                {"scene_id": s.scene_id, "beat": s.beat, "title": s.title, "order": s.order}
                for s in self.scenes
            ],
            "shot_list": [
                s.to_dict() for scene in self.scenes for s in scene.shots
            ],
            "character_assignments": dict(self.character_assignments),
            "environment_assignments": dict(self.environment_assignments),
            "camera_plan": dict(self.camera_plan),
            "audio_plan": dict(self.audio_plan),
            "render_plan": dict(self.render_plan),
            "export_plan": dict(self.export_plan),
            "total_runtime_sec": self.total_runtime_sec,
            "shot_count": self.shot_count,
            "accuracy_score": self.accuracy_score,
        }


@dataclass
class DirectorObservability:
    director_job_id: str
    project_id: str | None = None
    scene_count: int = 0
    shot_count: int = 0
    runtime_sec: float = 0.0
    processing_time_ms: float = 0.0
    queue_time_ms: float = 0.0
    errors: list[str] = field(default_factory=list)
    retry_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DirectorIntelligenceJob:
    job_id: str
    project_id: str
    state: DirectorJobState
    prompt: str
    analysis: StoryAnalysis | None = None
    production_plan: ProductionPlan | None = None
    integrations: dict[str, Any] = field(default_factory=dict)
    observability: DirectorObservability | None = None
    queue_position: int | None = None
    retry_count: int = 0
    production_ready: bool = True
    accuracy_score: float = 0.0
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def summary(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "project_id": self.project_id,
            "state": self.state,
            "format_type": self.analysis.format_type if self.analysis else None,
            "genre": self.analysis.genre if self.analysis else None,
            "scene_count": len(self.production_plan.scenes) if self.production_plan else 0,
            "shot_count": self.production_plan.shot_count if self.production_plan else 0,
            "runtime_sec": self.production_plan.total_runtime_sec if self.production_plan else 0.0,
            "accuracy_score": self.accuracy_score,
            "queue_position": self.queue_position,
            "retry_count": self.retry_count,
            "production_ready": self.production_ready,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.summary(),
            "prompt": self.prompt,
            "analysis": self.analysis.to_dict() if self.analysis else None,
            "production_plan": self.production_plan.to_dict() if self.production_plan else None,
            "integrations": dict(self.integrations),
            "observability": self.observability.to_dict() if self.observability else None,
            "metadata": dict(self.metadata),
            "error": self.error,
            "version": self.version,
        }
