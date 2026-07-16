"""Models for Scene Breakdown & Shot Generation Engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class DetailedShot:
    scene_number: int
    shot_number: int
    shot_type: str
    camera_angle: str
    lens: str
    camera_movement: str
    lighting: list[str]
    environment: str
    weather: str
    time: str
    character_position: str
    character_emotion: str
    facial_expression: str
    body_language: str
    color_palette: list[str]
    depth_of_field: str
    composition: str
    transition_type: str
    sound_design: list[str]
    music_mood: str
    estimated_duration_seconds: float
    purpose: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DetailedScene:
    scene_number: int
    scene_purpose: str
    title: str
    estimated_duration_seconds: float
    environment: str
    weather: str
    time: str
    character_emotion: str
    lighting: list[str]
    color_palette: list[str]
    music_mood: str
    transition_type: str
    shots: list[DetailedShot] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scene_number": self.scene_number,
            "scene_purpose": self.scene_purpose,
            "title": self.title,
            "estimated_duration_seconds": self.estimated_duration_seconds,
            "environment": self.environment,
            "weather": self.weather,
            "time": self.time,
            "character_emotion": self.character_emotion,
            "lighting": self.lighting,
            "color_palette": self.color_palette,
            "music_mood": self.music_mood,
            "transition_type": self.transition_type,
            "shots": [s.to_dict() for s in self.shots],
        }


@dataclass
class TimelineBeat:
    scene_number: int
    shot_number: int
    start_seconds: float
    end_seconds: float
    label: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProductionBreakdown:
    """Canonical Production JSON: Scenes[], Shots[], Timeline, Estimated Runtime."""

    prompt: str
    scenes: list[DetailedScene]
    shots: list[DetailedShot]
    timeline: list[TimelineBeat]
    estimated_runtime_seconds: float
    expected_video_length: str
    pacing_notes: list[str] = field(default_factory=list)
    story_rhythm: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "Production": {
                "prompt": self.prompt,
                "Scenes": [s.to_dict() for s in self.scenes],
                "Shots": [s.to_dict() for s in self.shots],
                "Timeline": [t.to_dict() for t in self.timeline],
                "EstimatedRuntime": self.estimated_runtime_seconds,
                "ExpectedVideoLength": self.expected_video_length,
                "PacingNotes": self.pacing_notes,
                "StoryRhythm": self.story_rhythm,
            }
        }
