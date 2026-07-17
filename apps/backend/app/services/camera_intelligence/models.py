"""Camera intelligence domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

CameraJobState = Literal[
    "queued",
    "preparing",
    "planning",
    "camera_analysis",
    "shot_generation",
    "completed",
    "failed",
    "cancelled",
    "retrying",
]


@dataclass
class SceneAnalysis:
    scene_type: str
    character_count: int
    character_positions: list[dict[str, Any]]
    scene_emotion: str
    story_progression: str
    environment: str
    lighting: str
    camera_movement_recommendation: str
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LensSelection:
    lens_id: str
    name: str
    focal_length_mm: float
    aperture: float
    depth_of_field: str
    use_case: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ShotPlan:
    shot_id: str
    shot_type: str
    framing: dict[str, Any]
    composition: dict[str, Any]
    camera_motion: dict[str, Any]
    lens: LensSelection
    duration_sec: float
    subject_tracking: bool = True
    face_tracking: bool = True
    auto_focus: bool = True
    rack_focus: bool = False
    zoom: float = 1.0
    shake_control: str = "stabilized"
    start_sec: float = 0.0
    end_sec: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "shot_id": self.shot_id,
            "shot_type": self.shot_type,
            "framing": dict(self.framing),
            "composition": dict(self.composition),
            "camera_motion": dict(self.camera_motion),
            "lens": self.lens.to_dict(),
            "duration_sec": self.duration_sec,
            "subject_tracking": self.subject_tracking,
            "face_tracking": self.face_tracking,
            "auto_focus": self.auto_focus,
            "rack_focus": self.rack_focus,
            "zoom": self.zoom,
            "shake_control": self.shake_control,
            "start_sec": self.start_sec,
            "end_sec": self.end_sec,
            "metadata": dict(self.metadata),
        }


@dataclass
class CameraTimelineEvent:
    event_id: str
    start_sec: float
    end_sec: float
    shot_id: str
    shot_type: str
    layer: str = "camera"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CameraObservability:
    camera_job_id: str
    shot_type: str | None = None
    lens_used: str | None = None
    scene_id: str | None = None
    processing_time_ms: float = 0.0
    queue_time_ms: float = 0.0
    errors: list[str] = field(default_factory=list)
    retry_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CameraIntelligenceJob:
    job_id: str
    state: CameraJobState
    prompt: str
    scene_id: str | None
    character_ids: list[str]
    analysis: SceneAnalysis | None
    shots: list[ShotPlan] = field(default_factory=list)
    timeline: list[CameraTimelineEvent] = field(default_factory=list)
    coverage: dict[str, Any] = field(default_factory=dict)
    integrations: dict[str, Any] = field(default_factory=dict)
    observability: CameraObservability | None = None
    queue_position: int | None = None
    retry_count: int = 0
    duration_sec: float = 0.0
    production_ready: bool = True
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def summary(self) -> dict[str, Any]:
        primary_shot = self.shots[0].shot_type if self.shots else None
        primary_lens = self.shots[0].lens.lens_id if self.shots else None
        return {
            "job_id": self.job_id,
            "state": self.state,
            "scene_id": self.scene_id,
            "character_ids": list(self.character_ids),
            "shot_count": len(self.shots),
            "primary_shot_type": primary_shot,
            "primary_lens": primary_lens,
            "duration_sec": self.duration_sec,
            "queue_position": self.queue_position,
            "retry_count": self.retry_count,
            "production_ready": self.production_ready,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.summary(),
            "prompt": self.prompt,
            "analysis": self.analysis.to_dict() if self.analysis else None,
            "shots": [s.to_dict() for s in self.shots],
            "timeline": [t.to_dict() for t in self.timeline],
            "coverage": dict(self.coverage),
            "integrations": dict(self.integrations),
            "observability": self.observability.to_dict() if self.observability else None,
            "metadata": dict(self.metadata),
            "error": self.error,
            "version": self.version,
        }
