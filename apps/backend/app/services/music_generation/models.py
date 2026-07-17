"""Music Generation domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

MusicJobState = Literal[
    "queued",
    "preparing",
    "composing",
    "generating",
    "mixing",
    "completed",
    "failed",
    "cancelled",
    "retrying",
]

MusicRole = Literal["background", "intro", "outro", "theme", "loop", "instrumental"]


@dataclass
class MusicControls:
    bpm: int = 90
    key: str = "Cm"
    mood: str = "dramatic"
    energy: float = 0.6  # 0–1
    intensity: float = 0.5  # 0–1
    duration_sec: float = 30.0
    instruments: list[str] = field(default_factory=list)
    loop: bool = False
    fade_in_sec: float = 1.0
    fade_out_sec: float = 2.0
    stems: list[str] = field(default_factory=lambda: ["drums", "bass", "melody", "pads"])

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MusicObservability:
    music_job_id: str
    genre: str
    bpm: int
    duration_sec: float
    mood: str
    processing_time_ms: float
    queue_time_ms: float
    provider: str = "simulation"
    retry_count: int = 0
    errors: list[str] = field(default_factory=list)
    log_events: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MusicJob:
    job_id: str
    engine: str
    version: str
    state: MusicJobState
    genre: str
    role: MusicRole
    title: str
    controls: MusicControls
    observability: MusicObservability
    library_id: str | None = None
    asset_url: str | None = None
    preview_url: str | None = None
    stem_urls: dict[str, str] = field(default_factory=dict)
    provider: str = "simulation"
    queue_position: int | None = None
    retry_count: int = 0
    music_version: int = 1
    production_ready: bool = False
    parent_audio_job_id: str | None = None
    parent_video_job_id: str | None = None
    parent_generation_id: str | None = None
    scene_emotion: str | None = None
    scene_duration_sec: float | None = None
    camera_motion: str | None = None
    story_beat: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "engine": self.engine,
            "version": self.version,
            "state": self.state,
            "genre": self.genre,
            "role": self.role,
            "title": self.title,
            "controls": self.controls.to_dict(),
            "observability": self.observability.to_dict(),
            "library_id": self.library_id,
            "asset_url": self.asset_url,
            "preview_url": self.preview_url,
            "stem_urls": dict(self.stem_urls),
            "provider": self.provider,
            "queue_position": self.queue_position,
            "retry_count": self.retry_count,
            "music_version": self.music_version,
            "production_ready": self.production_ready,
            "parent_audio_job_id": self.parent_audio_job_id,
            "parent_video_job_id": self.parent_video_job_id,
            "parent_generation_id": self.parent_generation_id,
            "scene_emotion": self.scene_emotion,
            "scene_duration_sec": self.scene_duration_sec,
            "camera_motion": self.camera_motion,
            "story_beat": self.story_beat,
            "metadata": dict(self.metadata),
            "history": list(self.history),
        }

    def summary(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "state": self.state,
            "genre": self.genre,
            "role": self.role,
            "bpm": self.controls.bpm,
            "key": self.controls.key,
            "mood": self.controls.mood,
            "energy": self.controls.energy,
            "duration_sec": self.controls.duration_sec,
            "loop": self.controls.loop,
            "music_version": self.music_version,
            "production_ready": self.production_ready,
            "retry_count": self.retry_count,
            "queue_position": self.queue_position,
            "processing_time_ms": self.observability.processing_time_ms,
            "queue_time_ms": self.observability.queue_time_ms,
            "provider": self.provider,
            "library_id": self.library_id,
            "asset_url": self.asset_url,
        }
