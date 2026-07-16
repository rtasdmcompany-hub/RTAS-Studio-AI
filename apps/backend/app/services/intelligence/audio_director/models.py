"""Models for AI Audio Director & Lip Sync Engine (planning only)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

AudioCategory = Literal[
    "music_video",
    "advertisement",
    "movie",
    "podcast",
    "islamic",
    "shorts",
    "documentary",
    "general",
]


@dataclass
class AudioDetection:
    language: str
    accent: str
    gender: str
    emotion: str
    speech_speed: str
    pause_timing: list[str]
    music_style: str
    volume_balance: dict[str, float]
    category: AudioCategory
    has_dialogue: bool
    has_narration: bool
    has_singing: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TimelineCue:
    start_sec: float
    end_sec: float
    label: str
    kind: str
    character_id: str | None = None
    emotion: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LipSyncCue:
    start_sec: float
    end_sec: float
    character_id: str
    phoneme_hint: str
    mouth_openness: float  # 0–1
    viseme: str
    dialogue_snippet: str
    sync_confidence: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AudioDirectorPlan:
    detection: AudioDetection
    voice_timeline: list[TimelineCue]
    music_timeline: list[TimelineCue]
    sfx_timeline: list[TimelineCue]
    lip_sync_timeline: list[LipSyncCue]
    narration_notes: list[str]
    dialogue_notes: list[str]
    silence_windows: list[dict[str, Any]]
    mix_notes: list[str]
    estimated_runtime_seconds: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "detection": self.detection.to_dict(),
            "voice_timeline": [c.to_dict() for c in self.voice_timeline],
            "music_timeline": [c.to_dict() for c in self.music_timeline],
            "sfx_timeline": [c.to_dict() for c in self.sfx_timeline],
            "lip_sync_timeline": [c.to_dict() for c in self.lip_sync_timeline],
            "narration_notes": self.narration_notes,
            "dialogue_notes": self.dialogue_notes,
            "silence_windows": self.silence_windows,
            "mix_notes": self.mix_notes,
            "estimated_runtime_seconds": self.estimated_runtime_seconds,
        }
