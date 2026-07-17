"""Voice Cloning & Character Voice domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

CloneJobState = Literal[
    "queued",
    "training",
    "preparing",
    "processing",
    "completed",
    "failed",
    "cancelled",
    "retrying",
]


@dataclass
class VoiceFingerprint:
    fingerprint_id: str
    checksum: str
    embedding_ref: str
    sample_rate: int
    duration_sec: float
    spectral_hash: str
    speaker_score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SpeakerProfile:
    speaker_id: str
    owner_id: str | None
    gender: str
    age_group: str
    language: str
    accent: str
    speaking_style: str
    emotion_profile: str
    fingerprint: VoiceFingerprint | None = None
    locked: bool = False
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "speaker_id": self.speaker_id,
            "owner_id": self.owner_id,
            "gender": self.gender,
            "age_group": self.age_group,
            "language": self.language,
            "accent": self.accent,
            "speaking_style": self.speaking_style,
            "emotion_profile": self.emotion_profile,
            "fingerprint": self.fingerprint.to_dict() if self.fingerprint else None,
            "locked": self.locked,
            "version": self.version,
            "metadata": dict(self.metadata),
        }


@dataclass
class CharacterVoiceProfile:
    character_id: str
    clone_id: str | None
    default_voice: str
    language: str
    accent: str
    speaking_style: str
    emotion_profile: str
    gender: str
    age_group: str
    voice_version: int
    voice_metadata: dict[str, Any] = field(default_factory=dict)
    voice_locked: bool = False
    speaker_id: str | None = None
    preview_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "character_id": self.character_id,
            "clone_id": self.clone_id,
            "default_voice": self.default_voice,
            "language": self.language,
            "accent": self.accent,
            "speaking_style": self.speaking_style,
            "emotion_profile": self.emotion_profile,
            "gender": self.gender,
            "age_group": self.age_group,
            "voice_version": self.voice_version,
            "voice_metadata": dict(self.voice_metadata),
            "voice_locked": self.voice_locked,
            "speaker_id": self.speaker_id,
            "preview_url": self.preview_url,
        }

    def restore_voice_kwargs(self) -> dict[str, Any]:
        """Arguments Character Memory restores on every generation."""
        return {
            "voice_id": self.default_voice,
            "language": self.language,
            "gender": self.gender,
            "clone_id": self.clone_id,
            "accent": self.accent,
            "speaking_style": self.speaking_style,
            "emotion_profile": self.emotion_profile,
            "voice_version": self.voice_version,
            "voice_locked": self.voice_locked,
        }


@dataclass
class CloneQuality:
    overall: float
    similarity: float
    clarity: float
    consistency: float
    grade: str
    speaker_verified: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CloneObservability:
    clone_id: str
    character_id: str | None
    voice_version: int
    training_duration_ms: float
    processing_time_ms: float
    queue_time_ms: float
    retry_count: int = 0
    errors: list[str] = field(default_factory=list)
    provider: str = "simulation"
    quality_score: float = 0.0
    log_events: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VoiceCloneJob:
    clone_id: str
    engine: str
    version: str
    state: CloneJobState
    owner_id: str | None
    character_id: str | None
    reference_url: str
    reference_checksum: str
    language: str
    accent: str
    speaking_style: str
    emotion_profile: str
    gender: str
    age_group: str
    speaker: SpeakerProfile | None
    fingerprint: VoiceFingerprint | None
    quality: CloneQuality
    observability: CloneObservability
    voice_locked: bool = False
    voice_version: int = 1
    preview_url: str | None = None
    asset_url: str | None = None
    provider: str = "simulation"
    queue_position: int | None = None
    retry_count: int = 0
    parent_generation_id: str | None = None
    parent_video_job_id: str | None = None
    production_ready: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)
    training_history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "clone_id": self.clone_id,
            "engine": self.engine,
            "version": self.version,
            "state": self.state,
            "owner_id": self.owner_id,
            "character_id": self.character_id,
            "reference_url": self.reference_url,
            "reference_checksum": self.reference_checksum,
            "language": self.language,
            "accent": self.accent,
            "speaking_style": self.speaking_style,
            "emotion_profile": self.emotion_profile,
            "gender": self.gender,
            "age_group": self.age_group,
            "speaker": self.speaker.to_dict() if self.speaker else None,
            "fingerprint": self.fingerprint.to_dict() if self.fingerprint else None,
            "quality": self.quality.to_dict(),
            "observability": self.observability.to_dict(),
            "voice_locked": self.voice_locked,
            "voice_version": self.voice_version,
            "preview_url": self.preview_url,
            "asset_url": self.asset_url,
            "provider": self.provider,
            "queue_position": self.queue_position,
            "retry_count": self.retry_count,
            "parent_generation_id": self.parent_generation_id,
            "parent_video_job_id": self.parent_video_job_id,
            "production_ready": self.production_ready,
            "metadata": dict(self.metadata),
            "history": list(self.history),
            "training_history": list(self.training_history),
        }

    def summary(self) -> dict[str, Any]:
        return {
            "clone_id": self.clone_id,
            "state": self.state,
            "character_id": self.character_id,
            "language": self.language,
            "gender": self.gender,
            "voice_version": self.voice_version,
            "voice_locked": self.voice_locked,
            "quality": self.quality.overall,
            "grade": self.quality.grade,
            "speaker_verified": self.quality.speaker_verified,
            "production_ready": self.production_ready,
            "retry_count": self.retry_count,
            "queue_position": self.queue_position,
            "training_duration_ms": self.observability.training_duration_ms,
            "processing_time_ms": self.observability.processing_time_ms,
            "queue_time_ms": self.observability.queue_time_ms,
            "provider": self.provider,
            "owner_id": self.owner_id,
        }
