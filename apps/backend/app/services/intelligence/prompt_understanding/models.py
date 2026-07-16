"""Structured production instructions from cinematic prompt understanding."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class CinematicPromptUnderstanding:
    """Director-grade parse of a user prompt into production instructions."""

    scene_type: str
    camera: list[str]
    lighting: list[str]
    lens: str
    movement: list[str]
    environment: str
    mood: str
    emotion: list[str]
    weather: str
    time: str
    color_palette: list[str]
    music_style: list[str]
    transition_style: str
    # Extended cinematic fields
    shot_types: list[str] = field(default_factory=list)
    visual_atmosphere: str = ""
    subject_count: int = 1
    category: str = "Movie Scene"
    color_grading: str = ""
    confidence: float = 0.5
    raw_prompt: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def production_instructions(self) -> dict[str, Any]:
        """Canonical structured output for orchestrator / clients."""
        return {
            "scene_type": self.scene_type,
            "camera": self.camera,
            "lighting": self.lighting,
            "lens": self.lens,
            "movement": self.movement,
            "environment": self.environment,
            "mood": self.mood,
            "emotion": self.emotion,
            "weather": self.weather,
            "time": self.time,
            "color_palette": self.color_palette,
            "music_style": self.music_style,
            "transition_style": self.transition_style,
            "shot_types": self.shot_types,
            "visual_atmosphere": self.visual_atmosphere,
            "subject_count": self.subject_count,
            "category": self.category,
            "color_grading": self.color_grading,
            "confidence": self.confidence,
        }
