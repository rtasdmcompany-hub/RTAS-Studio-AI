"""Audio Timeline domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

TimelineJobState = Literal[
    "queued",
    "preparing",
    "synchronizing",
    "optimizing",
    "rendering",
    "completed",
    "failed",
    "cancelled",
    "retrying",
]

TrackKind = Literal[
    "voice",
    "music",
    "ambient",
    "sfx",
    "foley",
    "narration",
    "transition",
]

SyncMode = Literal[
    "scene",
    "shot",
    "frame",
    "beat",
    "emotion",
    "lip_sync",
    "auto",
]


@dataclass
class BeatMarker:
    marker_id: str
    time_sec: float
    beat_index: int
    intensity: float = 0.5
    bar: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TimelineEvent:
    event_id: str
    track_id: str
    kind: str
    start_sec: float
    end_sec: float
    label: str | None = None
    scene_id: str | None = None
    shot_id: str | None = None
    frame: int | None = None
    emotion: str | None = None
    asset_url: str | None = None
    gain_db: float = 0.0
    locked: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TimelineTrack:
    track_id: str
    kind: TrackKind
    name: str
    events: list[TimelineEvent] = field(default_factory=list)
    gain_db: float = 0.0
    muted: bool = False
    locked: bool = False
    snap_enabled: bool = True
    order: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "track_id": self.track_id,
            "kind": self.kind,
            "name": self.name,
            "events": [e.to_dict() for e in self.events],
            "gain_db": self.gain_db,
            "muted": self.muted,
            "locked": self.locked,
            "snap_enabled": self.snap_enabled,
            "order": self.order,
        }


@dataclass
class AudioLayer:
    layer_id: str
    name: str
    track_ids: list[str]
    blend_mode: str = "mix"
    gain_db: float = 0.0
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SyncMetadata:
    mode: SyncMode
    fps: float
    frame_accuracy_ms: float
    sync_accuracy: float
    scene_count: int
    shot_count: int
    beat_count: int
    lip_sync_aligned: bool = False
    emotion_aligned: bool = False
    camera_music_aligned: bool = False
    dynamic_balance: bool = True
    snap_grid_ms: float = 33.33
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TimelineObservability:
    timeline_id: str
    scene_count: int
    track_count: int
    sync_accuracy: float
    processing_time_ms: float
    queue_time_ms: float
    retry_count: int = 0
    errors: list[str] = field(default_factory=list)
    provider: str = "simulation"
    log_events: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TimelineVersion:
    version: int
    label: str
    snapshot: dict[str, Any]
    created_at: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TimelineJob:
    job_id: str
    engine: str
    version: str
    state: TimelineJobState
    tracks: list[TimelineTrack]
    layers: list[AudioLayer]
    beat_markers: list[BeatMarker]
    sync: SyncMetadata
    observability: TimelineObservability
    duration_sec: float = 0.0
    fps: float = 24.0
    locked: bool = False
    snap_enabled: bool = True
    auto_align: bool = True
    production_ready: bool = False
    export_url: str | None = None
    master_timeline_url: str | None = None
    provider: str = "simulation"
    timeline_version: int = 1
    versions: list[TimelineVersion] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)
    retry_count: int = 0
    queue_position: int | None = None
    parent_voice_job_id: str | None = None
    parent_music_job_id: str | None = None
    parent_sfx_job_id: str | None = None
    parent_mix_job_id: str | None = None
    parent_localization_job_id: str | None = None
    parent_video_job_id: str | None = None
    parent_generation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "engine": self.engine,
            "version": self.version,
            "state": self.state,
            "duration_sec": self.duration_sec,
            "fps": self.fps,
            "track_count": len(self.tracks),
            "layer_count": len(self.layers),
            "beat_count": len(self.beat_markers),
            "scene_count": self.sync.scene_count,
            "shot_count": self.sync.shot_count,
            "sync_accuracy": self.sync.sync_accuracy,
            "locked": self.locked,
            "snap_enabled": self.snap_enabled,
            "auto_align": self.auto_align,
            "production_ready": self.production_ready,
            "export_url": self.export_url,
            "master_timeline_url": self.master_timeline_url,
            "timeline_version": self.timeline_version,
            "retry_count": self.retry_count,
            "queue_position": self.queue_position,
            "parent_voice_job_id": self.parent_voice_job_id,
            "parent_music_job_id": self.parent_music_job_id,
            "parent_sfx_job_id": self.parent_sfx_job_id,
            "parent_mix_job_id": self.parent_mix_job_id,
            "parent_localization_job_id": self.parent_localization_job_id,
            "parent_video_job_id": self.parent_video_job_id,
            "parent_generation_id": self.parent_generation_id,
            "observability": self.observability.to_dict(),
            "sync": self.sync.to_dict(),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.summary(),
            "tracks": [t.to_dict() for t in self.tracks],
            "layers": [layer.to_dict() for layer in self.layers],
            "beat_markers": [b.to_dict() for b in self.beat_markers],
            "versions": [v.to_dict() for v in self.versions],
            "history": list(self.history),
            "metadata": dict(self.metadata),
            "provider": self.provider,
        }
