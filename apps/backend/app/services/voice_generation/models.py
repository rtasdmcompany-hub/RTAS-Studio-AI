"""Voice Generation Engine domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

VoiceJobState = Literal[
    "queued",
    "preparing",
    "generating",
    "completed",
    "failed",
    "cancelled",
    "retrying",
]


@dataclass
class VoiceControls:
    speed: float = 1.0  # 0.5–2.0
    pitch: float = 0.0  # -12..+12 semitones-ish
    volume: float = 1.0  # 0.0–2.0
    pause_ms: int = 0
    pronunciation_hints: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VoiceQuality:
    overall: float
    naturalness: float
    clarity: float
    prosody: float
    grade: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VoiceExportPackage:
    ready: bool
    formats: list[str] = field(default_factory=lambda: ["wav", "mp3", "ogg"])
    primary_format: str = "wav"
    filename: str = "rtas_voice.wav"
    ssml_included: bool = True
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VoiceObservability:
    voice_job_id: str
    voice_model: str
    language: str
    duration_sec: float
    processing_time_ms: float
    queue_time_ms: float
    retry_count: int = 0
    errors: list[str] = field(default_factory=list)
    log_events: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VoiceGenerationJob:
    job_id: str
    engine: str
    version: str
    text: str
    language: str
    voice_id: str
    gender: str
    state: VoiceJobState
    controls: VoiceControls
    ssml: str
    estimated_duration_sec: float
    quality: VoiceQuality
    export: VoiceExportPackage
    observability: VoiceObservability
    metadata: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)
    asset_url: str | None = None
    provider: str = "simulation"
    queue_position: int | None = None
    retry_count: int = 0
    parent_audio_job_id: str | None = None
    parent_generation_id: str | None = None
    production_ready: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "engine": self.engine,
            "version": self.version,
            "text": self.text,
            "language": self.language,
            "voice_id": self.voice_id,
            "gender": self.gender,
            "state": self.state,
            "controls": self.controls.to_dict(),
            "ssml": self.ssml,
            "estimated_duration_sec": self.estimated_duration_sec,
            "quality": self.quality.to_dict(),
            "export": self.export.to_dict(),
            "observability": self.observability.to_dict(),
            "metadata": dict(self.metadata),
            "history": list(self.history),
            "asset_url": self.asset_url,
            "provider": self.provider,
            "queue_position": self.queue_position,
            "retry_count": self.retry_count,
            "parent_audio_job_id": self.parent_audio_job_id,
            "parent_generation_id": self.parent_generation_id,
            "production_ready": self.production_ready,
        }

    def summary(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "state": self.state,
            "language": self.language,
            "voice_id": self.voice_id,
            "gender": self.gender,
            "duration_sec": self.estimated_duration_sec,
            "quality": self.quality.overall,
            "grade": self.quality.grade,
            "production_ready": self.production_ready,
            "export_ready": self.export.ready,
            "retry_count": self.retry_count,
            "queue_position": self.queue_position,
            "processing_time_ms": self.observability.processing_time_ms,
            "queue_time_ms": self.observability.queue_time_ms,
            "provider": self.provider,
            "voice_model": self.observability.voice_model,
        }
