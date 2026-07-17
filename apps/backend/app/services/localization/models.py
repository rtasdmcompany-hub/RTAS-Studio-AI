"""Localization / dubbing domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

LocalizationJobState = Literal[
    "queued",
    "preparing",
    "translating",
    "voice_generation",
    "lip_sync",
    "subtitle_generation",
    "completed",
    "failed",
    "cancelled",
    "retrying",
]

JobKind = Literal["translate", "dub", "localize"]


@dataclass
class SpeakerMapEntry:
    speaker_id: str
    character_id: str | None
    source_voice_id: str | None
    clone_id: str | None
    gender: str
    accent: str
    preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SubtitleCue:
    cue_id: str
    start_sec: float
    end_sec: float
    text: str
    language: str
    speaker_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AudioTrack:
    track_id: str
    language: str
    kind: str  # dialogue | narration | original
    asset_url: str | None
    duration_sec: float
    speaker_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TranslationSegment:
    segment_id: str
    source_text: str
    translated_text: str
    source_language: str
    target_language: str
    start_sec: float
    end_sec: float
    speaker_id: str | None = None
    from_memory: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LocalizationObservability:
    translation_job_id: str
    source_language: str
    target_language: str
    speaker_count: int
    processing_time_ms: float
    queue_time_ms: float
    retry_count: int = 0
    errors: list[str] = field(default_factory=list)
    provider: str = "simulation"
    log_events: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LocalizationJob:
    job_id: str
    engine: str
    version: str
    state: LocalizationJobState
    kind: JobKind
    source_language: str
    target_language: str
    source_text: str
    translated_text: str
    segments: list[TranslationSegment]
    speakers: list[SpeakerMapEntry]
    subtitles: list[SubtitleCue]
    captions: list[SubtitleCue]
    audio_tracks: list[AudioTrack]
    observability: LocalizationObservability
    lip_sync_metadata: dict[str, Any] = field(default_factory=dict)
    accent_profile: str = "neutral"
    voice_preserved: bool = True
    subtitle_url: str | None = None
    caption_url: str | None = None
    dubbed_audio_url: str | None = None
    provider: str = "simulation"
    queue_position: int | None = None
    retry_count: int = 0
    localization_version: int = 1
    production_ready: bool = False
    parent_voice_job_id: str | None = None
    parent_clone_id: str | None = None
    parent_video_job_id: str | None = None
    parent_generation_id: str | None = None
    character_memory: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "engine": self.engine,
            "version": self.version,
            "state": self.state,
            "kind": self.kind,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "source_text": self.source_text,
            "translated_text": self.translated_text,
            "segments": [s.to_dict() for s in self.segments],
            "speakers": [s.to_dict() for s in self.speakers],
            "subtitles": [c.to_dict() for c in self.subtitles],
            "captions": [c.to_dict() for c in self.captions],
            "audio_tracks": [t.to_dict() for t in self.audio_tracks],
            "observability": self.observability.to_dict(),
            "lip_sync_metadata": dict(self.lip_sync_metadata),
            "accent_profile": self.accent_profile,
            "voice_preserved": self.voice_preserved,
            "subtitle_url": self.subtitle_url,
            "caption_url": self.caption_url,
            "dubbed_audio_url": self.dubbed_audio_url,
            "provider": self.provider,
            "queue_position": self.queue_position,
            "retry_count": self.retry_count,
            "localization_version": self.localization_version,
            "production_ready": self.production_ready,
            "parent_voice_job_id": self.parent_voice_job_id,
            "parent_clone_id": self.parent_clone_id,
            "parent_video_job_id": self.parent_video_job_id,
            "parent_generation_id": self.parent_generation_id,
            "character_memory": list(self.character_memory),
            "metadata": dict(self.metadata),
            "history": list(self.history),
        }

    def summary(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "state": self.state,
            "kind": self.kind,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "speaker_count": len(self.speakers),
            "segments": len(self.segments),
            "subtitle_cues": len(self.subtitles),
            "caption_cues": len(self.captions),
            "audio_tracks": len(self.audio_tracks),
            "voice_preserved": self.voice_preserved,
            "production_ready": self.production_ready,
            "retry_count": self.retry_count,
            "queue_position": self.queue_position,
            "processing_time_ms": self.observability.processing_time_ms,
            "queue_time_ms": self.observability.queue_time_ms,
            "provider": self.provider,
            "dubbed_audio_url": self.dubbed_audio_url,
        }
