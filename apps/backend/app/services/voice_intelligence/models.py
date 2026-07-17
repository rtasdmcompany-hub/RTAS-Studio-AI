"""Voice intelligence domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

DialogueRole = Literal[
    "narrator",
    "character_a",
    "character_b",
    "character_c",
    "group",
    "internal_thought",
    "voice_over",
]

EmotionTone = Literal[
    "happy",
    "sad",
    "angry",
    "romantic",
    "motivational",
    "emotional",
    "fear",
    "serious",
    "calm",
    "suspense",
    "excited",
]

AgeGroup = Literal["child", "teen", "young_adult", "adult", "senior"]

VOICE_PROFILE_FIELDS = (
    "voice_id",
    "gender",
    "age_group",
    "language",
    "accent",
    "speaking_speed",
    "pitch",
    "energy",
    "emotion_style",
    "narration_style",
)


@dataclass
class CharacterVoiceProfile:
    voice_id: str
    gender: str
    age_group: AgeGroup
    language: str
    accent: str
    speaking_speed: float  # relative 0.5–1.5
    pitch: float  # relative 0.5–1.5
    energy: float  # 0–1
    emotion_style: EmotionTone
    narration_style: str
    character_slot: str | None = None
    character_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DialogueLine:
    line_id: str
    index: int
    text: str
    role: DialogueRole
    emotion: EmotionTone
    character_slot: str | None = None
    voice_id: str | None = None
    start_sec: float = 0.0
    end_sec: float = 0.0
    speaking_duration_sec: float = 0.0
    pause_after_sec: float = 0.0
    dramatic_pause_sec: float = 0.0
    breathing_pause_sec: float = 0.0
    is_narration: bool = False
    is_internal: bool = False
    is_voice_over: bool = False
    is_group: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TimingPlan:
    total_duration_sec: float
    speaking_duration_sec: float
    pause_duration_sec: float
    dramatic_pause_sec: float
    breathing_pause_sec: float
    transition_timing_sec: float
    overlap_prevented: bool
    line_timings: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ConsistencyReport:
    project_id: str
    consistent: bool
    consistency_score: float
    same_voice_across_scenes: bool
    same_accent: bool
    emotion_continuity: bool
    no_unexpected_switching: bool
    dialogue_synchronized: bool
    issues: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VoiceIntelligenceJob:
    project_id: str
    job_id: str
    script: str
    language: str
    lines: list[DialogueLine] = field(default_factory=list)
    voice_profiles: dict[str, CharacterVoiceProfile] = field(default_factory=dict)
    timing: TimingPlan | None = None
    narration_summary: dict[str, Any] = field(default_factory=dict)
    consistency: ConsistencyReport | None = None
    version: int = 1
    production_ready: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "job_id": self.job_id,
            "language": self.language,
            "line_count": len(self.lines),
            "voice_count": len(self.voice_profiles),
            "total_duration_sec": self.timing.total_duration_sec if self.timing else None,
            "version": self.version,
            "production_ready": self.production_ready,
            "consistency_score": (
                self.consistency.consistency_score if self.consistency else None
            ),
            "consistent": self.consistency.consistent if self.consistency else None,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.summary(),
            "script": self.script,
            "lines": [ln.to_dict() for ln in self.lines],
            "voice_profiles": {k: v.to_dict() for k, v in self.voice_profiles.items()},
            "timing": self.timing.to_dict() if self.timing else None,
            "narration_summary": dict(self.narration_summary),
            "consistency": self.consistency.to_dict() if self.consistency else None,
            "metadata": dict(self.metadata),
        }
