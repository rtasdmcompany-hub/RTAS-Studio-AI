"""Sprint 4 shared models — Character Memory, Director, Continuity, Timeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class CharacterMemory:
    character_id: str
    gender: str
    age: str
    hair: str
    beard: str
    skin_tone: str
    face_shape: str
    eye_color: str
    outfit: str
    accessories: list[str] = field(default_factory=list)
    reference_image_urls: list[str] = field(default_factory=list)
    face_embedding_ref: str | None = None  # future InstantID / embedding hook
    locked_traits: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def identity_lock_prompt(self) -> str:
        accessories = ", ".join(self.accessories) if self.accessories else "none"
        return (
            f"IDENTITY LOCK [{self.character_id}]: "
            f"{self.gender}, age {self.age}, {self.hair} hair, beard={self.beard}, "
            f"skin={self.skin_tone}, face={self.face_shape}, eyes={self.eye_color}, "
            f"outfit={self.outfit}, accessories={accessories}. "
            f"Keep identical face, hair, clothing, body proportions across all scenes."
        )


@dataclass
class ConsistencyReport:
    locked_character_ids: list[str]
    face_locked: bool
    hair_locked: bool
    clothing_locked: bool
    body_locked: bool
    proportions_locked: bool
    overrides_allowed: bool
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DirectorDecision:
    shot_type: str
    emotional_beat: str
    emphasis: str
    transition_in: str
    transition_out: str
    pacing: str
    dramatic_timing: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DirectorPlan:
    shot_order: list[str]
    emotional_pacing: list[str]
    cinematic_rhythm: str
    transition_style: str
    dramatic_timing_notes: list[str]
    scene_emphasis: list[str]
    decisions: list[DirectorDecision] = field(default_factory=list)
    director_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "shot_order": self.shot_order,
            "emotional_pacing": self.emotional_pacing,
            "cinematic_rhythm": self.cinematic_rhythm,
            "transition_style": self.transition_style,
            "dramatic_timing_notes": self.dramatic_timing_notes,
            "scene_emphasis": self.scene_emphasis,
            "decisions": [d.to_dict() for d in self.decisions],
            "director_notes": self.director_notes,
        }


@dataclass
class ContinuityState:
    character_positions: dict[str, str]
    time_of_day: str
    weather: str
    location: str
    wardrobe: dict[str, str]
    objects: list[str]
    emotion_arc: list[str]
    contradictions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TimelineNode:
    kind: str  # scene | shot | transition
    id: str
    label: str
    duration_seconds: int
    parent_id: str | None = None
    character_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CinematicTimeline:
    nodes: list[TimelineNode]
    total_duration_seconds: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "total_duration_seconds": self.total_duration_seconds,
        }


@dataclass
class ProductionPackage:
    prompt: str
    enhanced_prompt: str
    scene_plan: list[dict[str, Any]]
    shot_plan: list[dict[str, Any]]
    camera_plan: list[dict[str, Any]]
    character_memory: list[dict[str, Any]]
    consistency: dict[str, Any]
    continuity: dict[str, Any]
    timeline: dict[str, Any]
    director_notes: list[str]
    director_plan: dict[str, Any]
    quality_report: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
