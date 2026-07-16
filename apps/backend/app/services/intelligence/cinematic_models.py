"""Sprint 5 — Cinematic AI Brain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class CinematicReasoning:
    story: str
    emotion: str
    genre: str
    character_arc: str
    audience: str
    production_style: str
    themes: list[str] = field(default_factory=list)
    logline: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VisualStylePlan:
    lighting: str
    color_palette: list[str]
    mood: str
    contrast: str
    film_stock_style: str
    lens_style: str
    camera_language: str
    reference_look: str  # Hollywood / Netflix / IMAX / etc.

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EmotionBeat:
    scene_index: int
    emotion: str
    intensity: float
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EmotionMap:
    primary_emotion: str
    beats: list[EmotionBeat]
    arc: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "primary_emotion": self.primary_emotion,
            "beats": [b.to_dict() for b in self.beats],
            "arc": self.arc,
        }


@dataclass
class MusicPlan:
    genre: str
    tempo_bpm: int
    energy: str
    emotion: str
    instrumentation: list[str]
    beat_transitions: list[str]
    cue_timing: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VoicePlan:
    gender: str
    age: str
    tone: str
    emotion: str
    speed: str
    pauses: list[str]
    emphasis: list[str]
    language: str
    accent: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SoundDesignPlan:
    ambient: list[str]
    foley: list[str]
    transitions: list[str]
    environmental_fx: list[str]
    background_layers: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CinematicQualityScore:
    story: float
    camera: float
    emotion: float
    prompt_quality: float
    character_consistency: float
    scene_continuity: float
    lighting: float
    visual_quality: float
    overall: float
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AutoImprovementResult:
    applied: bool
    improvements: list[str]
    enhanced_prompt: str
    intent_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MasterAIPlan:
    project_summary: str
    story_analysis: dict[str, Any]
    character_memory: list[dict[str, Any]]
    scene_plan: list[dict[str, Any]]
    shot_plan: list[dict[str, Any]]
    camera_plan: list[dict[str, Any]]
    lighting_plan: dict[str, Any]
    music_plan: dict[str, Any]
    voice_plan: dict[str, Any]
    sound_plan: dict[str, Any]
    timeline: dict[str, Any]
    quality_report: dict[str, Any]
    export_plan: dict[str, Any]
    visual_style: dict[str, Any]
    emotion_map: dict[str, Any]
    director_plan: dict[str, Any]
    continuity: dict[str, Any]
    auto_improvement: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
