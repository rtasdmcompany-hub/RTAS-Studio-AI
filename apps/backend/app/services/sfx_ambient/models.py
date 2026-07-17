"""SFX & Ambient domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

SfxJobState = Literal[
    "queued",
    "preparing",
    "searching",
    "generating",
    "layering",
    "completed",
    "failed",
    "cancelled",
    "retrying",
]

JobKind = Literal["sfx", "ambient", "foley", "scene"]


@dataclass
class SpatialMeta:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    distance: float = 1.0  # 0 near … 1 far
    pan: float = 0.0  # -1 left … +1 right

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AudioLayer:
    layer_id: str
    category: str
    kind: str
    volume: float
    start_sec: float
    end_sec: float
    loop: bool
    fade_in_sec: float
    fade_out_sec: float
    spatial: SpatialMeta
    asset_url: str | None = None
    library_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "layer_id": self.layer_id,
            "category": self.category,
            "kind": self.kind,
            "volume": self.volume,
            "start_sec": self.start_sec,
            "end_sec": self.end_sec,
            "loop": self.loop,
            "fade_in_sec": self.fade_in_sec,
            "fade_out_sec": self.fade_out_sec,
            "spatial": self.spatial.to_dict(),
            "asset_url": self.asset_url,
            "library_id": self.library_id,
        }


@dataclass
class TimelineEvent:
    event_id: str
    scene_id: str | None
    at_sec: float
    category: str
    action: str  # play | stop | fade | duck
    layer_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "scene_id": self.scene_id,
            "at_sec": self.at_sec,
            "category": self.category,
            "action": self.action,
            "layer_id": self.layer_id,
            "metadata": dict(self.metadata),
        }


@dataclass
class EnvironmentProfile:
    environment: str
    mood: str
    energy: float
    recommended_categories: list[str]
    scene_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "environment": self.environment,
            "mood": self.mood,
            "energy": self.energy,
            "recommended_categories": list(self.recommended_categories),
            "scene_id": self.scene_id,
            "metadata": dict(self.metadata),
        }


@dataclass
class SfxObservability:
    sfx_job_id: str
    scene_id: str | None
    environment: str
    duration_sec: float
    processing_time_ms: float
    queue_time_ms: float
    retry_count: int = 0
    errors: list[str] = field(default_factory=list)
    asset_usage: list[str] = field(default_factory=list)
    provider: str = "simulation"
    log_events: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SfxJob:
    job_id: str
    engine: str
    version: str
    state: SfxJobState
    kind: JobKind
    categories: list[str]
    environment: EnvironmentProfile
    layers: list[AudioLayer]
    timeline_events: list[TimelineEvent]
    observability: SfxObservability
    duration_sec: float = 12.0
    volume: float = 0.5
    loop: bool = False
    fade_in_sec: float = 0.5
    fade_out_sec: float = 1.0
    asset_url: str | None = None
    preview_url: str | None = None
    library_ids: list[str] = field(default_factory=list)
    provider: str = "simulation"
    queue_position: int | None = None
    retry_count: int = 0
    audio_version: int = 1
    production_ready: bool = False
    parent_audio_job_id: str | None = None
    parent_music_job_id: str | None = None
    parent_video_job_id: str | None = None
    parent_generation_id: str | None = None
    scene_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "engine": self.engine,
            "version": self.version,
            "state": self.state,
            "kind": self.kind,
            "categories": list(self.categories),
            "environment": self.environment.to_dict(),
            "layers": [L.to_dict() for L in self.layers],
            "timeline_events": [e.to_dict() for e in self.timeline_events],
            "observability": self.observability.to_dict(),
            "duration_sec": self.duration_sec,
            "volume": self.volume,
            "loop": self.loop,
            "fade_in_sec": self.fade_in_sec,
            "fade_out_sec": self.fade_out_sec,
            "asset_url": self.asset_url,
            "preview_url": self.preview_url,
            "library_ids": list(self.library_ids),
            "provider": self.provider,
            "queue_position": self.queue_position,
            "retry_count": self.retry_count,
            "audio_version": self.audio_version,
            "production_ready": self.production_ready,
            "parent_audio_job_id": self.parent_audio_job_id,
            "parent_music_job_id": self.parent_music_job_id,
            "parent_video_job_id": self.parent_video_job_id,
            "parent_generation_id": self.parent_generation_id,
            "scene_id": self.scene_id,
            "metadata": dict(self.metadata),
            "history": list(self.history),
        }

    def summary(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "state": self.state,
            "kind": self.kind,
            "scene_id": self.scene_id,
            "environment": self.environment.environment,
            "categories": list(self.categories),
            "layers": len(self.layers),
            "timeline_events": len(self.timeline_events),
            "duration_sec": self.duration_sec,
            "volume": self.volume,
            "loop": self.loop,
            "audio_version": self.audio_version,
            "production_ready": self.production_ready,
            "retry_count": self.retry_count,
            "queue_position": self.queue_position,
            "processing_time_ms": self.observability.processing_time_ms,
            "queue_time_ms": self.observability.queue_time_ms,
            "provider": self.provider,
            "asset_usage": list(self.observability.asset_usage),
        }
