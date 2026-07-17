"""Data models for the AI Audio Production Engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

AudioJobState = Literal[
    "queued",
    "preparing",
    "generating",
    "processing",
    "completed",
    "failed",
    "cancelled",
    "retrying",
]


@dataclass
class VoiceClip:
    clip_id: str
    text: str
    character: str | None = None
    language: str = "en"
    start_sec: float = 0.0
    end_sec: float = 0.0
    provider_hint: str = "simulation"
    asset_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MusicClip:
    clip_id: str
    style: str
    mood: str = "neutral"
    start_sec: float = 0.0
    end_sec: float = 0.0
    loop: bool = False
    provider_hint: str = "simulation"
    asset_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AmbientClip:
    clip_id: str
    label: str
    intensity: float = 0.5
    start_sec: float = 0.0
    end_sec: float = 0.0
    asset_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SfxClip:
    clip_id: str
    label: str
    category: str = "foley"
    start_sec: float = 0.0
    duration_sec: float = 0.5
    asset_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TimelineTrack:
    track_id: str
    kind: Literal["voice", "music", "ambient", "sfx"]
    clips: list[dict[str, Any]] = field(default_factory=list)
    gain_db: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AudioMetadata:
    job_id: str
    sample_rate: int = 48000
    channels: int = 2
    bit_depth: int = 24
    loudness_lufs: float = -14.0
    duration_sec: float = 0.0
    languages: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationResult:
    passed: bool
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExportPackage:
    ready: bool
    formats: list[str] = field(default_factory=lambda: ["wav", "mp3", "aac"])
    primary_format: str = "wav"
    filename: str = "rtas_audio.wav"
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ObservabilitySnapshot:
    generation_id: str | None
    provider: str
    queue_time_ms: float
    duration_ms: float
    latency_ms: float
    errors: list[str] = field(default_factory=list)
    log_events: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AudioEnginePlan:
    job_id: str
    engine: str
    version: str
    prompt: str
    state: AudioJobState
    voice_clips: list[VoiceClip]
    music_clips: list[MusicClip]
    ambient_clips: list[AmbientClip]
    sfx_clips: list[SfxClip]
    timeline: list[TimelineTrack]
    metadata: AudioMetadata
    validation: ValidationResult
    export: ExportPackage
    observability: ObservabilitySnapshot
    history: list[dict[str, Any]] = field(default_factory=list)
    queue_position: int | None = None
    retry_count: int = 0
    parent_generation_id: str | None = None
    production_ready: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "engine": self.engine,
            "version": self.version,
            "prompt": self.prompt,
            "state": self.state,
            "voice_clips": [c.to_dict() for c in self.voice_clips],
            "music_clips": [c.to_dict() for c in self.music_clips],
            "ambient_clips": [c.to_dict() for c in self.ambient_clips],
            "sfx_clips": [c.to_dict() for c in self.sfx_clips],
            "timeline": [t.to_dict() for t in self.timeline],
            "metadata": self.metadata.to_dict(),
            "validation": self.validation.to_dict(),
            "export": self.export.to_dict(),
            "observability": self.observability.to_dict(),
            "history": list(self.history),
            "queue_position": self.queue_position,
            "retry_count": self.retry_count,
            "parent_generation_id": self.parent_generation_id,
            "production_ready": self.production_ready,
        }

    def summary(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "engine": self.engine,
            "version": self.version,
            "state": self.state,
            "production_ready": self.production_ready,
            "voice_clips": len(self.voice_clips),
            "music_clips": len(self.music_clips),
            "ambient_clips": len(self.ambient_clips),
            "sfx_clips": len(self.sfx_clips),
            "timeline_tracks": len(self.timeline),
            "duration_sec": self.metadata.duration_sec,
            "validation_passed": self.validation.passed,
            "export_ready": self.export.ready,
            "retry_count": self.retry_count,
            "queue_position": self.queue_position,
            "latency_ms": self.observability.latency_ms,
            "provider": self.observability.provider,
        }
