"""Export domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

ExportJobState = Literal[
    "queued",
    "preparing",
    "packaging",
    "exporting",
    "compressing",
    "uploading",
    "completed",
    "failed",
    "cancelled",
    "retrying",
]

AudioFormat = Literal["wav", "mp3", "flac", "aac", "ogg"]
VideoFormat = Literal["mp4", "mov", "mkv", "webm"]
MetadataFormat = Literal["json", "xml"]


@dataclass
class ExportProfile:
    profile_id: str
    platform: str
    label: str
    video_format: VideoFormat
    audio_format: AudioFormat
    resolution: str
    width: int
    height: int
    video_bitrate_kbps: int
    audio_bitrate_kbps: int
    audio_loudness_lufs: float
    video_codec: str
    audio_codec: str
    fps: float = 30.0
    aspect_ratio: str = "16:9"
    metadata_format: MetadataFormat = "json"
    max_duration_sec: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExportAsset:
    asset_id: str
    kind: str  # video | audio | subtitle | caption | thumbnail | metadata | package
    format: str
    url: str
    size_bytes: int
    checksum: str
    mime_type: str
    verified: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DownloadTicket:
    ticket_id: str
    export_job_id: str
    signed_url: str
    expires_at: float
    authorized: bool
    download_count: int = 0
    max_downloads: int = 10
    token: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExportObservability:
    export_job_id: str
    export_format: str
    resolution: str
    processing_time_ms: float
    queue_time_ms: float
    download_count: int = 0
    export_size_bytes: int = 0
    retry_count: int = 0
    errors: list[str] = field(default_factory=list)
    provider: str = "simulation"
    log_events: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExportAnalytics:
    export_job_id: str
    platform: str
    format: str
    size_bytes: int
    processing_time_ms: float
    download_count: int
    success: bool
    compression_ratio: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExportVersion:
    version: int
    label: str
    snapshot: dict[str, Any]
    created_at: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExportJob:
    job_id: str
    engine: str
    version: str
    state: ExportJobState
    profile: ExportProfile
    assets: list[ExportAsset]
    observability: ExportObservability
    analytics: ExportAnalytics
    package_url: str | None = None
    download_url: str | None = None
    signed_url: str | None = None
    expires_at: float | None = None
    watermark: bool = False
    batch_id: str | None = None
    production_ready: bool = False
    verified: bool = False
    resume_token: str | None = None
    export_version: int = 1
    versions: list[ExportVersion] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)
    delivery_logs: list[dict[str, Any]] = field(default_factory=list)
    download_history: list[dict[str, Any]] = field(default_factory=list)
    retry_count: int = 0
    queue_position: int | None = None
    provider: str = "simulation"
    parent_timeline_job_id: str | None = None
    parent_video_job_id: str | None = None
    parent_localization_job_id: str | None = None
    parent_mix_job_id: str | None = None
    parent_generation_id: str | None = None
    formats: list[str] = field(default_factory=list)
    quality: str = "high"
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "engine": self.engine,
            "version": self.version,
            "state": self.state,
            "platform": self.profile.platform,
            "profile_id": self.profile.profile_id,
            "resolution": self.profile.resolution,
            "video_format": self.profile.video_format,
            "audio_format": self.profile.audio_format,
            "formats": list(self.formats),
            "quality": self.quality,
            "package_url": self.package_url,
            "download_url": self.download_url,
            "signed_url": self.signed_url,
            "expires_at": self.expires_at,
            "watermark": self.watermark,
            "batch_id": self.batch_id,
            "production_ready": self.production_ready,
            "verified": self.verified,
            "export_version": self.export_version,
            "asset_count": len(self.assets),
            "export_size_bytes": self.observability.export_size_bytes,
            "download_count": self.observability.download_count,
            "retry_count": self.retry_count,
            "queue_position": self.queue_position,
            "parent_timeline_job_id": self.parent_timeline_job_id,
            "parent_video_job_id": self.parent_video_job_id,
            "parent_localization_job_id": self.parent_localization_job_id,
            "parent_mix_job_id": self.parent_mix_job_id,
            "parent_generation_id": self.parent_generation_id,
            "observability": self.observability.to_dict(),
            "analytics": self.analytics.to_dict(),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.summary(),
            "profile": self.profile.to_dict(),
            "assets": [a.to_dict() for a in self.assets],
            "versions": [v.to_dict() for v in self.versions],
            "history": list(self.history),
            "delivery_logs": list(self.delivery_logs),
            "download_history": list(self.download_history),
            "resume_token": self.resume_token,
            "provider": self.provider,
            "metadata": dict(self.metadata),
        }
