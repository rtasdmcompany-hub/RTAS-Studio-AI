"""Mixing & Mastering domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

MixJobState = Literal[
    "queued",
    "preparing",
    "mixing",
    "mastering",
    "quality_check",
    "completed",
    "failed",
    "cancelled",
    "retrying",
]

JobKind = Literal["mix", "master", "mix_master"]


@dataclass
class ChannelGains:
    voice: float = 1.0
    music: float = 0.65
    sfx: float = 0.75
    ambient: float = 0.45

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MixProfile:
    dialogue_priority: bool = True
    music_ducking_db: float = -8.0
    sfx_balance: float = 0.75
    ambient_level: float = 0.45
    stereo_pan_voice: float = 0.0
    stereo_pan_music: float = 0.0
    compression_ratio: float = 3.0
    limiter_ceiling_db: float = -1.0
    eq_low_gain_db: float = 0.0
    eq_mid_gain_db: float = 1.0
    eq_high_gain_db: float = 0.5
    gains: ChannelGains = field(default_factory=ChannelGains)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dialogue_priority": self.dialogue_priority,
            "music_ducking_db": self.music_ducking_db,
            "sfx_balance": self.sfx_balance,
            "ambient_level": self.ambient_level,
            "stereo_pan_voice": self.stereo_pan_voice,
            "stereo_pan_music": self.stereo_pan_music,
            "compression_ratio": self.compression_ratio,
            "limiter_ceiling_db": self.limiter_ceiling_db,
            "eq_low_gain_db": self.eq_low_gain_db,
            "eq_mid_gain_db": self.eq_mid_gain_db,
            "eq_high_gain_db": self.eq_high_gain_db,
            "gains": self.gains.to_dict(),
        }


@dataclass
class MasterProfile:
    target_lufs: float = -14.0
    true_peak_ceiling_dbtp: float = -1.0
    stereo_width: float = 1.15
    tonal_balance: str = "broadcast"
    noise_reduction: bool = True
    dynamic_range_target_db: float = 8.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LoudnessReport:
    integrated_lufs: float
    short_term_lufs: float
    momentary_lufs: float
    true_peak_dbtp: float
    peak_dbfs: float
    loudness_range_lu: float
    normalized: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FrequencyAnalysis:
    low_energy: float
    mid_energy: float
    high_energy: float
    spectral_centroid_hz: float
    tonal_balance_score: float
    bands: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "low_energy": self.low_energy,
            "mid_energy": self.mid_energy,
            "high_energy": self.high_energy,
            "spectral_centroid_hz": self.spectral_centroid_hz,
            "tonal_balance_score": self.tonal_balance_score,
            "bands": dict(self.bands),
        }


@dataclass
class AudioQualityReport:
    lufs: float
    peak_dbfs: float
    true_peak_dbtp: float
    dynamic_range_db: float
    stereo_width: float
    noise_floor_db: float
    frequency_balance: float
    clarity_score: float
    overall_score: float
    grade: str
    production_ready: bool
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MixObservability:
    mix_job_id: str
    master_job_id: str | None
    processing_time_ms: float
    queue_time_ms: float
    loudness_lufs: float
    quality_score: float
    retry_count: int = 0
    errors: list[str] = field(default_factory=list)
    provider: str = "simulation"
    log_events: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MixMasterJob:
    job_id: str
    engine: str
    version: str
    state: MixJobState
    kind: JobKind
    mix_profile: MixProfile
    master_profile: MasterProfile
    loudness: LoudnessReport
    frequency: FrequencyAnalysis
    quality: AudioQualityReport
    observability: MixObservability
    mix_job_id: str | None = None
    master_job_id: str | None = None
    asset_url: str | None = None
    master_url: str | None = None
    export_format: str = "wav"
    export_sample_rate: int = 48000
    export_bit_depth: int = 24
    provider: str = "simulation"
    queue_position: int | None = None
    retry_count: int = 0
    audio_version: int = 1
    production_ready: bool = False
    parent_voice_job_id: str | None = None
    parent_music_job_id: str | None = None
    parent_sfx_job_id: str | None = None
    parent_audio_job_id: str | None = None
    parent_video_job_id: str | None = None
    parent_generation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "engine": self.engine,
            "version": self.version,
            "state": self.state,
            "kind": self.kind,
            "mix_job_id": self.mix_job_id or self.job_id,
            "master_job_id": self.master_job_id,
            "mix_profile": self.mix_profile.to_dict(),
            "master_profile": self.master_profile.to_dict(),
            "loudness": self.loudness.to_dict(),
            "frequency": self.frequency.to_dict(),
            "quality": self.quality.to_dict(),
            "observability": self.observability.to_dict(),
            "asset_url": self.asset_url,
            "master_url": self.master_url,
            "export_format": self.export_format,
            "export_sample_rate": self.export_sample_rate,
            "export_bit_depth": self.export_bit_depth,
            "provider": self.provider,
            "queue_position": self.queue_position,
            "retry_count": self.retry_count,
            "audio_version": self.audio_version,
            "production_ready": self.production_ready,
            "parent_voice_job_id": self.parent_voice_job_id,
            "parent_music_job_id": self.parent_music_job_id,
            "parent_sfx_job_id": self.parent_sfx_job_id,
            "parent_audio_job_id": self.parent_audio_job_id,
            "parent_video_job_id": self.parent_video_job_id,
            "parent_generation_id": self.parent_generation_id,
            "metadata": dict(self.metadata),
            "history": list(self.history),
        }

    def summary(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "mix_job_id": self.mix_job_id or self.job_id,
            "master_job_id": self.master_job_id,
            "state": self.state,
            "kind": self.kind,
            "lufs": self.loudness.integrated_lufs,
            "true_peak_dbtp": self.loudness.true_peak_dbtp,
            "quality_score": self.quality.overall_score,
            "grade": self.quality.grade,
            "clarity_score": self.quality.clarity_score,
            "stereo_width": self.quality.stereo_width,
            "production_ready": self.production_ready,
            "retry_count": self.retry_count,
            "queue_position": self.queue_position,
            "processing_time_ms": self.observability.processing_time_ms,
            "queue_time_ms": self.observability.queue_time_ms,
            "provider": self.provider,
            "master_url": self.master_url,
            "export_format": self.export_format,
        }
