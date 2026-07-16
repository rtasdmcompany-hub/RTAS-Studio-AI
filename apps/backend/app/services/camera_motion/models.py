"""Camera Motion Engine — dataclasses."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

CameraMotionKind = Literal[
    "dolly",
    "crane",
    "drone",
    "orbit",
    "slider",
    "tracking",
    "push_in",
    "pull_out",
    "pov",
    "steadicam",
    "handheld",
    "static",
]


@dataclass
class CameraKeyframe:
    t: float  # 0–1 normalized within cue, or absolute sec via start/end
    position: tuple[float, float, float]  # x, y, z relative units
    look_at: tuple[float, float, float]
    fov_deg: float
    roll_deg: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "t": self.t,
            "position": list(self.position),
            "look_at": list(self.look_at),
            "fov_deg": self.fov_deg,
            "roll_deg": self.roll_deg,
        }


@dataclass
class CameraMotionCue:
    start_sec: float
    end_sec: float
    kind: CameraMotionKind
    intensity: float  # 0–1
    speed: float  # 0–1 relative
    ease: str  # ease_in_out / linear / ease_out
    direction: str  # forward / back / left / right / up / down / around
    subject_lock: bool
    shake: float  # handheld micro-shake 0–1
    keyframes: list[CameraKeyframe] = field(default_factory=list)
    lens_hint: str = ""
    notes: str = ""
    scene_index: int = 0
    shot_index: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "start_sec": self.start_sec,
            "end_sec": self.end_sec,
            "kind": self.kind,
            "intensity": self.intensity,
            "speed": self.speed,
            "ease": self.ease,
            "direction": self.direction,
            "subject_lock": self.subject_lock,
            "shake": self.shake,
            "keyframes": [k.to_dict() for k in self.keyframes],
            "lens_hint": self.lens_hint,
            "notes": self.notes,
            "scene_index": self.scene_index,
            "shot_index": self.shot_index,
        }


@dataclass
class AdaptiveDecision:
    chosen: CameraMotionKind
    reason: str
    alternatives: list[CameraMotionKind] = field(default_factory=list)
    factors: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SceneCameraMotion:
    scene_index: int
    title: str
    duration_seconds: float
    primary_motion: CameraMotionKind
    adaptive: AdaptiveDecision
    cues: list[CameraMotionCue] = field(default_factory=list)
    framing: str = ""
    angle: str = ""
    directives: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scene_index": self.scene_index,
            "title": self.title,
            "duration_seconds": self.duration_seconds,
            "primary_motion": self.primary_motion,
            "adaptive": self.adaptive.to_dict(),
            "cues": [c.to_dict() for c in self.cues],
            "framing": self.framing,
            "angle": self.angle,
            "directives": self.directives,
        }


@dataclass
class CameraMotionPlan:
    job_id: str
    prompt: str
    total_duration_seconds: float
    scenes: list[SceneCameraMotion]
    timeline: list[dict[str, Any]] = field(default_factory=list)
    adaptive_logic: dict[str, Any] = field(default_factory=dict)
    director_integration: dict[str, Any] = field(default_factory=dict)
    motion_integration: dict[str, Any] = field(default_factory=dict)
    scene_planner_integration: dict[str, Any] = field(default_factory=dict)
    provider_directives: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "prompt": self.prompt,
            "total_duration_seconds": self.total_duration_seconds,
            "scenes": [s.to_dict() for s in self.scenes],
            "timeline": self.timeline,
            "adaptive_logic": self.adaptive_logic,
            "director_integration": self.director_integration,
            "motion_integration": self.motion_integration,
            "scene_planner_integration": self.scene_planner_integration,
            "provider_directives": self.provider_directives,
        }

    def summary(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "scenes": len(self.scenes),
            "total_duration_seconds": self.total_duration_seconds,
            "primary_motions": [s.primary_motion for s in self.scenes],
            "cue_count": sum(len(s.cues) for s in self.scenes),
            "adaptive_mode": (self.adaptive_logic or {}).get("mode"),
            "directives": self.provider_directives[:12],
        }
