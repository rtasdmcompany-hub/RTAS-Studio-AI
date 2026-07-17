"""Production Ready Video Engine — dataclasses."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

StageName = Literal[
    "prompt",
    "director",
    "scene",
    "shot",
    "camera",
    "generation",
    "rendering",
    "export",
    "download",
]

StageStatus = Literal["pending", "ready", "running", "passed", "failed", "skipped", "recovered"]


@dataclass
class PipelineStage:
    name: StageName
    order: int
    status: StageStatus
    duration_ms: float
    score: float  # 0–1
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    retries: int = 0
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class QualityScore:
    overall: float
    prompt: float
    director: float
    scene: float
    shot: float
    camera: float
    generation: float
    rendering: float
    export: float
    consistency: float
    production_ready: bool
    grade: str  # A/B/C/D/F
    breakdown: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationResult:
    passed: bool
    checks: dict[str, bool]
    issues: list[dict[str, Any]]
    blockers: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PerformanceMetrics:
    total_ms: float
    stage_ms: dict[str, float]
    throughput_scenes_per_min: float
    gpu_assigned: int
    cache_hits: int
    memory_target_mb: int | None
    p95_stage_ms: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MonitorSnapshot:
    healthy: bool
    pipeline_status: str
    active_alerts: list[str]
    stage_health: dict[str, str]
    error_rate: float
    retry_rate: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AnalyticsSnapshot:
    scenes: int
    shots: int
    cameras: int
    characters: int
    effects: list[str]
    camera_motions: list[str]
    gpu_skus: list[str]
    export_formats: list[str]
    quality_overall: float
    production_ready: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RecoveryPlan:
    enabled: bool
    auto_retry: bool
    max_attempts: int
    recovered_stages: list[str]
    pending_retries: list[dict[str, Any]]
    strategy: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StressTestResult:
    ran: bool
    iterations: int
    success_rate: float
    avg_ms: float
    max_ms: float
    failures: int
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DownloadPackage:
    ready: bool
    formats: list[str]
    primary_url_hint: str
    filename: str
    checksum_hint: str
    size_estimate_mb: float
    expires_hint: str
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VideoEnginePlan:
    job_id: str
    engine: str
    version: str
    prompt: str
    stages: list[PipelineStage]
    quality: QualityScore
    validation: ValidationResult
    performance: PerformanceMetrics
    monitoring: MonitorSnapshot
    analytics: AnalyticsSnapshot
    recovery: RecoveryPlan
    stress: StressTestResult
    download: DownloadPackage
    timeline: list[dict[str, Any]] = field(default_factory=list)
    integrations: dict[str, Any] = field(default_factory=dict)
    provider_directives: list[str] = field(default_factory=list)
    production_ready: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "engine": self.engine,
            "version": self.version,
            "prompt": self.prompt,
            "stages": [s.to_dict() for s in self.stages],
            "quality": self.quality.to_dict(),
            "validation": self.validation.to_dict(),
            "performance": self.performance.to_dict(),
            "monitoring": self.monitoring.to_dict(),
            "analytics": self.analytics.to_dict(),
            "recovery": self.recovery.to_dict(),
            "stress": self.stress.to_dict(),
            "download": self.download.to_dict(),
            "timeline": self.timeline,
            "integrations": self.integrations,
            "provider_directives": self.provider_directives,
            "production_ready": self.production_ready,
        }

    def summary(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "engine": self.engine,
            "version": self.version,
            "production_ready": self.production_ready,
            "quality_score": self.quality.overall,
            "quality_grade": self.quality.grade,
            "validation_passed": self.validation.passed,
            "stages_passed": sum(1 for s in self.stages if s.status in ("passed", "recovered")),
            "stages_total": len(self.stages),
            "total_ms": self.performance.total_ms,
            "download_ready": self.download.ready,
            "alerts": self.monitoring.active_alerts[:6],
            "directives": self.provider_directives[:10],
        }
