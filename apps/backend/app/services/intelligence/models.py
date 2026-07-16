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

    def to_dict(self) -> dict[str, Any]:
        return {
            "intelligence": self.intelligence.to_dict(),
            "enhancement": self.enhancement.to_dict(),
            "scenes": [s.to_dict() for s in self.scenes],
            "cameras": [c.to_dict() for c in self.cameras],
            "shots": [s.to_dict() for s in self.shots],
            "quality": self.quality.to_dict(),
            "export": self.export.to_dict(),
        }
