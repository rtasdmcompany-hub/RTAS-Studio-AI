"""Motion Intelligence Engine — dataclasses."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

LocomotionKind = Literal[
    "walking",
    "running",
    "sitting",
    "standing",
    "turning",
    "looking",
    "idle",
]

HandKind = Literal[
    "gesture",
    "point",
    "hold",
    "reach",
    "wave",
    "rest",
    "emphasize",
]

BodyKind = Literal[
    "weight_shift",
    "lean",
    "shoulder_roll",
    "breath",
    "posture",
    "twist",
    "crouch",
]


@dataclass
class LocomotionCue:
    start_sec: float
    end_sec: float
    kind: LocomotionKind
    intensity: float  # 0–1
    direction: str  # forward / left / right / back / toward_camera / away
    speed: float  # relative 0–1
    character_id: str | None = None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GazeCue:
    start_sec: float
    end_sec: float
    target: str  # camera / character / object / environment / offscreen
    yaw: float
    pitch: float
    hold: bool = True
    character_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HandMotionCue:
    start_sec: float
    end_sec: float
    kind: HandKind
    side: Literal["left", "right", "both"]
    intensity: float
    character_id: str | None = None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BodyMotionCue:
    start_sec: float
    end_sec: float
    kind: BodyKind
    intensity: float
    axis: str = "center"  # center / left / right / forward / back
    character_id: str | None = None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NaturalAnimationHint:
    """Natural human animation constraints for providers / animators."""

    ease_in_out: bool = True
    avoid_robotic: bool = True
    micro_movements: bool = True
    breath_cycle_sec: float = 4.0
    weight_transfer: bool = True
    secondary_motion: bool = True
    foot_contact_lock: bool = True
    head_follows_gaze: bool = True
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SceneMotionPlan:
    scene_index: int
    title: str
    duration_seconds: float
    primary_locomotion: LocomotionKind
    locomotion: list[LocomotionCue] = field(default_factory=list)
    gaze: list[GazeCue] = field(default_factory=list)
    hand_motion: list[HandMotionCue] = field(default_factory=list)
    body_motion: list[BodyMotionCue] = field(default_factory=list)
    camera_sync: list[str] = field(default_factory=list)
    director_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scene_index": self.scene_index,
            "title": self.title,
            "duration_seconds": self.duration_seconds,
            "primary_locomotion": self.primary_locomotion,
            "locomotion": [c.to_dict() for c in self.locomotion],
            "gaze": [c.to_dict() for c in self.gaze],
            "hand_motion": [c.to_dict() for c in self.hand_motion],
            "body_motion": [c.to_dict() for c in self.body_motion],
            "camera_sync": self.camera_sync,
            "director_notes": self.director_notes,
        }


@dataclass
class MotionIntelligencePlan:
    job_id: str
    prompt: str
    total_duration_seconds: float
    character_ids: list[str]
    walking_styles: dict[str, str]
    scenes: list[SceneMotionPlan]
    natural: NaturalAnimationHint
    director_integration: dict[str, Any] = field(default_factory=dict)
    camera_integration: dict[str, Any] = field(default_factory=dict)
    character_integration: dict[str, Any] = field(default_factory=dict)
    scene_planner_integration: dict[str, Any] = field(default_factory=dict)
    timeline: list[dict[str, Any]] = field(default_factory=list)
    animation_directives: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "prompt": self.prompt,
            "total_duration_seconds": self.total_duration_seconds,
            "character_ids": self.character_ids,
            "walking_styles": self.walking_styles,
            "scenes": [s.to_dict() for s in self.scenes],
            "natural": self.natural.to_dict(),
            "director_integration": self.director_integration,
            "camera_integration": self.camera_integration,
            "character_integration": self.character_integration,
            "scene_planner_integration": self.scene_planner_integration,
            "timeline": self.timeline,
            "animation_directives": self.animation_directives,
        }

    def summary(self) -> dict[str, Any]:
        primary = [s.primary_locomotion for s in self.scenes]
        return {
            "job_id": self.job_id,
            "scenes": len(self.scenes),
            "total_duration_seconds": self.total_duration_seconds,
            "primary_locomotion": primary,
            "locomotion_cues": sum(len(s.locomotion) for s in self.scenes),
            "gaze_cues": sum(len(s.gaze) for s in self.scenes),
            "hand_cues": sum(len(s.hand_motion) for s in self.scenes),
            "body_cues": sum(len(s.body_motion) for s in self.scenes),
            "characters": self.character_ids[:8],
            "natural": self.natural.to_dict(),
            "directives": self.animation_directives[:12],
        }
