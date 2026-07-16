"""Shared dataclasses for the Real AI intelligence stack."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class PromptIntelligenceResult:
    language: str
    category: str
    style: str
    emotion: str
    camera_requirements: list[str]
    lighting: str
    cinematic_genre: str
    estimated_duration_seconds: int
    missing_information: list[str]
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PromptEnhancementResult:
    original_prompt: str
    enhanced_prompt: str
    improvements: list[str]
    intent_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ScenePlan:
    index: int
    title: str
    duration_seconds: int
    description: str
    environment: str
    characters: list[str]
    actions: list[str]
    transitions: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CameraPlan:
    scene_index: int
    lens: str
    focal_length_mm: int
    movement: str
    framing: str
    angle: str
    depth: str
    cinematic_motion: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ShotPlan:
    scene_index: int
    shot_index: int
    title: str
    duration_seconds: int
    description: str
    camera: dict[str, Any]
    action: str
    dialogue_hint: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class QualityCheckResult:
    passed: bool
    score: float
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExportPlan:
    format: str
    resolution: str
    container: str
    audio_mix: str
    delivery_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class IntelligencePipelineResult:
    intelligence: PromptIntelligenceResult
    enhancement: PromptEnhancementResult
    scenes: list[ScenePlan]
    cameras: list[CameraPlan]
    shots: list[ShotPlan]
    quality: QualityCheckResult
    export: ExportPlan
    # Sprint 4 — Character Memory + AI Director package
    character_memory: list[dict[str, Any]] = field(default_factory=list)
    consistency: dict[str, Any] = field(default_factory=dict)
    continuity: dict[str, Any] = field(default_factory=dict)
    director_plan: dict[str, Any] = field(default_factory=dict)
    timeline: dict[str, Any] = field(default_factory=dict)
    production_package: dict[str, Any] = field(default_factory=dict)
    # Sprint 5 — Cinematic AI Brain
    cinematic_reasoning: dict[str, Any] = field(default_factory=dict)
    visual_style: dict[str, Any] = field(default_factory=dict)
    emotion_map: dict[str, Any] = field(default_factory=dict)
    music_plan: dict[str, Any] = field(default_factory=dict)
    voice_plan: dict[str, Any] = field(default_factory=dict)
    sound_plan: dict[str, Any] = field(default_factory=dict)
    cinematic_quality: dict[str, Any] = field(default_factory=dict)
    auto_improvement: dict[str, Any] = field(default_factory=dict)
    master_ai_plan: dict[str, Any] = field(default_factory=dict)
    # Cinematic Prompt Understanding Engine
    prompt_understanding: dict[str, Any] = field(default_factory=dict)
    # Sprint 6 — Scene Breakdown & Shot Generation
    scene_breakdown: dict[str, Any] = field(default_factory=dict)
    # Sprint 8 — Character Consistency Engine
    character_consistency: dict[str, Any] = field(default_factory=dict)
    # Sprint 9 — AI Audio Director & Lip Sync
    audio_director: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "intelligence": self.intelligence.to_dict(),
            "enhancement": self.enhancement.to_dict(),
            "scenes": [s.to_dict() for s in self.scenes],
            "cameras": [c.to_dict() for c in self.cameras],
            "shots": [s.to_dict() for s in self.shots],
            "quality": self.quality.to_dict(),
            "export": self.export.to_dict(),
            "character_memory": self.character_memory,
            "consistency": self.consistency,
            "continuity": self.continuity,
            "director_plan": self.director_plan,
            "timeline": self.timeline,
            "production_package": self.production_package,
            "cinematic_reasoning": self.cinematic_reasoning,
            "visual_style": self.visual_style,
            "emotion_map": self.emotion_map,
            "music_plan": self.music_plan,
            "voice_plan": self.voice_plan,
            "sound_plan": self.sound_plan,
            "cinematic_quality": self.cinematic_quality,
            "auto_improvement": self.auto_improvement,
            "master_ai_plan": self.master_ai_plan,
            "prompt_understanding": self.prompt_understanding,
            "scene_breakdown": self.scene_breakdown,
            "character_consistency": self.character_consistency,
            "audio_director": self.audio_director,
        }
