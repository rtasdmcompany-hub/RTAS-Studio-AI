"""Audio pipeline domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

PipelineJobState = Literal[
    "queued",
    "running",
    "validating",
    "completed",
    "failed",
    "cancelled",
    "retrying",
]


@dataclass
class StageResult:
    stage: str
    status: str
    job_id: str | None = None
    duration_ms: float = 0.0
    summary: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class QualityChecks:
    voice_quality: float
    music_quality: float
    audio_synchronization: float
    loudness_lufs: float
    dynamic_range: float
    noise_score: float
    clipping_score: float
    timeline_accuracy: float
    subtitle_accuracy: float
    localization_accuracy: float
    overall_score: float
    passed: bool
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PerformanceMetrics:
    total_processing_time_ms: float
    queue_time_ms: float
    export_time_ms: float
    download_time_ms: float
    memory_mb_estimate: float
    cpu_percent_estimate: float
    gpu_percent_estimate: float | None
    concurrent_jobs: int = 1
    stage_timings_ms: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PipelineObservability:
    pipeline_job_id: str
    stages_completed: int
    stages_total: int
    success_rate: float
    failure_rate: float
    retry_count: int
    processing_time_ms: float
    queue_time_ms: float
    errors: list[str] = field(default_factory=list)
    log_events: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PipelineJob:
    job_id: str
    engine: str
    version: str
    state: PipelineJobState
    prompt: str
    stages: list[StageResult]
    quality: QualityChecks
    performance: PerformanceMetrics
    observability: PipelineObservability
    production_ready: bool = False
    download_url: str | None = None
    export_job_id: str | None = None
    timeline_job_id: str | None = None
    localization_job_id: str | None = None
    voice_job_id: str | None = None
    music_job_id: str | None = None
    sfx_job_id: str | None = None
    mix_job_id: str | None = None
    clone_id: str | None = None
    platform: str = "youtube"
    parent_generation_id: str | None = None
    retry_count: int = 0
    queue_position: int | None = None
    provider: str = "simulation"
    metadata: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)

    def summary(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "engine": self.engine,
            "version": self.version,
            "state": self.state,
            "prompt": self.prompt[:200],
            "stages_completed": sum(1 for s in self.stages if s.status == "completed"),
            "stages_total": len(self.stages),
            "quality_score": self.quality.overall_score,
            "quality_passed": self.quality.passed,
            "production_ready": self.production_ready,
            "download_url": self.download_url,
            "export_job_id": self.export_job_id,
            "timeline_job_id": self.timeline_job_id,
            "localization_job_id": self.localization_job_id,
            "voice_job_id": self.voice_job_id,
            "music_job_id": self.music_job_id,
            "sfx_job_id": self.sfx_job_id,
            "mix_job_id": self.mix_job_id,
            "clone_id": self.clone_id,
            "platform": self.platform,
            "parent_generation_id": self.parent_generation_id,
            "retry_count": self.retry_count,
            "queue_position": self.queue_position,
            "performance": self.performance.to_dict(),
            "observability": self.observability.to_dict(),
            "quality": self.quality.to_dict(),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.summary(),
            "stages": [s.to_dict() for s in self.stages],
            "history": list(self.history),
            "metadata": dict(self.metadata),
            "provider": self.provider,
        }
