"""Physics Engine — dataclasses."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

PhysicsEffectKind = Literal[
    "hair_motion",
    "cloth_motion",
    "rain",
    "smoke",
    "dust",
    "wind",
    "explosion",
    "water",
    "fire",
    "particles",
    "gravity",
]


@dataclass
class ForceField:
    """Global or local force influencing soft bodies / particles."""

    kind: Literal["gravity", "wind", "turbulence", "drag", "buoyancy"]
    vector: tuple[float, float, float]  # x, y, z
    strength: float  # 0–1+
    turbulence: float = 0.0
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "vector": list(self.vector),
            "strength": self.strength,
            "turbulence": self.turbulence,
            "notes": self.notes,
        }


@dataclass
class ParticleSystem:
    name: str
    emitter: str  # point / volume / surface / character_hair / cloth
    count: int
    lifetime_sec: float
    size: float
    velocity: tuple[float, float, float]
    spread: float
    gravity_scale: float
    drag: float
    color_hint: str = ""
    collision: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "emitter": self.emitter,
            "count": self.count,
            "lifetime_sec": self.lifetime_sec,
            "size": self.size,
            "velocity": list(self.velocity),
            "spread": self.spread,
            "gravity_scale": self.gravity_scale,
            "drag": self.drag,
            "color_hint": self.color_hint,
            "collision": self.collision,
        }


@dataclass
class SoftBodySim:
    kind: Literal["hair", "cloth"]
    stiffness: float
    damping: float
    wind_response: float
    gravity_scale: float
    collision: bool = True
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PhysicsCue:
    start_sec: float
    end_sec: float
    kind: PhysicsEffectKind
    intensity: float
    forces: list[ForceField] = field(default_factory=list)
    particles: list[ParticleSystem] = field(default_factory=list)
    soft_body: SoftBodySim | None = None
    params: dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    scene_index: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "start_sec": self.start_sec,
            "end_sec": self.end_sec,
            "kind": self.kind,
            "intensity": self.intensity,
            "forces": [f.to_dict() for f in self.forces],
            "particles": [p.to_dict() for p in self.particles],
            "soft_body": self.soft_body.to_dict() if self.soft_body else None,
            "params": self.params,
            "notes": self.notes,
            "scene_index": self.scene_index,
        }


@dataclass
class ScenePhysicsPlan:
    scene_index: int
    title: str
    duration_seconds: float
    active_effects: list[PhysicsEffectKind]
    cues: list[PhysicsCue] = field(default_factory=list)
    gravity: ForceField | None = None
    wind: ForceField | None = None
    directives: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scene_index": self.scene_index,
            "title": self.title,
            "duration_seconds": self.duration_seconds,
            "active_effects": list(self.active_effects),
            "cues": [c.to_dict() for c in self.cues],
            "gravity": self.gravity.to_dict() if self.gravity else None,
            "wind": self.wind.to_dict() if self.wind else None,
            "directives": self.directives,
        }


@dataclass
class PhysicsPlan:
    job_id: str
    prompt: str
    total_duration_seconds: float
    scenes: list[ScenePhysicsPlan]
    global_gravity: ForceField
    timeline: list[dict[str, Any]] = field(default_factory=list)
    particle_summary: dict[str, Any] = field(default_factory=dict)
    director_integration: dict[str, Any] = field(default_factory=dict)
    scene_planner_integration: dict[str, Any] = field(default_factory=dict)
    motion_integration: dict[str, Any] = field(default_factory=dict)
    provider_directives: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "prompt": self.prompt,
            "total_duration_seconds": self.total_duration_seconds,
            "scenes": [s.to_dict() for s in self.scenes],
            "global_gravity": self.global_gravity.to_dict(),
            "timeline": self.timeline,
            "particle_summary": self.particle_summary,
            "director_integration": self.director_integration,
            "scene_planner_integration": self.scene_planner_integration,
            "motion_integration": self.motion_integration,
            "provider_directives": self.provider_directives,
        }

    def summary(self) -> dict[str, Any]:
        effects: list[str] = []
        for s in self.scenes:
            effects.extend(s.active_effects)
        return {
            "job_id": self.job_id,
            "scenes": len(self.scenes),
            "total_duration_seconds": self.total_duration_seconds,
            "effects": sorted(set(effects)),
            "cue_count": sum(len(s.cues) for s in self.scenes),
            "particle_systems": (self.particle_summary or {}).get("systems", 0),
            "gravity": self.global_gravity.strength,
            "directives": self.provider_directives[:12],
        }
