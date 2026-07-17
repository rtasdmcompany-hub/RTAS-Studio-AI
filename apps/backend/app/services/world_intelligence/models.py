"""World / environment / weather / lighting domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

WorldJobState = Literal[
    "queued",
    "preparing",
    "world_analysis",
    "environment_generation",
    "lighting_optimization",
    "completed",
    "failed",
    "cancelled",
    "retrying",
]

WORLD_CONSISTENCY_TRAITS = (
    "location",
    "buildings",
    "roads",
    "trees",
    "background_objects",
    "sky",
    "weather",
    "time_of_day",
    "lighting",
    "environmental_assets",
)


@dataclass
class WeatherProfile:
    weather_id: str
    mood_sync: str
    intensity: float
    precipitation: float
    visibility: float
    wind: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LightingProfile:
    lighting_id: str
    style: str
    soft_hard: str
    rim: bool
    hdr: bool
    shadows: str
    reflections: float
    gi_strength: float
    color_temp_k: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EnvironmentBlueprint:
    environment_id: str
    location_id: str
    category: str
    assets: dict[str, Any]
    sky: str
    time_of_day: str
    weather: WeatherProfile
    lighting: LightingProfile

    def to_dict(self) -> dict[str, Any]:
        return {
            "environment_id": self.environment_id,
            "location_id": self.location_id,
            "category": self.category,
            "assets": dict(self.assets),
            "sky": self.sky,
            "time_of_day": self.time_of_day,
            "weather": self.weather.to_dict(),
            "lighting": self.lighting.to_dict(),
        }

    def fingerprint(self) -> str:
        import hashlib

        payload = "|".join(
            [
                self.environment_id,
                self.location_id,
                self.category,
                self.sky,
                self.time_of_day,
                self.weather.weather_id,
                self.lighting.lighting_id,
            ]
        )
        return hashlib.sha256(payload.encode()).hexdigest()[:24]


@dataclass
class WorldAnalysis:
    scene_type: str
    recommended_environment: str
    recommended_weather: str
    recommended_time: str
    mood: str
    confidence: float
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ConsistencyReport:
    world_id: str
    consistent: bool
    score: float
    preserved_traits: list[str] = field(default_factory=list)
    drift_flags: list[str] = field(default_factory=list)
    no_continuity_breaks: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WorldObservability:
    environment_job_id: str
    world_id: str | None = None
    scene_id: str | None = None
    weather_type: str | None = None
    lighting_profile: str | None = None
    processing_time_ms: float = 0.0
    queue_time_ms: float = 0.0
    errors: list[str] = field(default_factory=list)
    retry_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WorldIntelligenceJob:
    job_id: str
    world_id: str
    state: WorldJobState
    prompt: str
    scene_id: str | None
    analysis: WorldAnalysis | None = None
    environment: EnvironmentBlueprint | None = None
    consistency: ConsistencyReport | None = None
    integrations: dict[str, Any] = field(default_factory=dict)
    observability: WorldObservability | None = None
    queue_position: int | None = None
    retry_count: int = 0
    production_ready: bool = True
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def summary(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "world_id": self.world_id,
            "state": self.state,
            "scene_id": self.scene_id,
            "environment": self.environment.category if self.environment else None,
            "weather": self.environment.weather.weather_id if self.environment else None,
            "lighting": self.environment.lighting.lighting_id if self.environment else None,
            "queue_position": self.queue_position,
            "retry_count": self.retry_count,
            "production_ready": self.production_ready,
            "consistent": self.consistency.consistent if self.consistency else None,
            "consistency_score": self.consistency.score if self.consistency else None,
        }

    def to_dict(self) -> dict[str, Any]:
        public_meta = {k: v for k, v in self.metadata.items() if not str(k).startswith("_")}
        return {
            **self.summary(),
            "prompt": self.prompt,
            "analysis": self.analysis.to_dict() if self.analysis else None,
            "environment_blueprint": self.environment.to_dict() if self.environment else None,
            "world_fingerprint": self.environment.fingerprint() if self.environment else None,
            "consistency": self.consistency.to_dict() if self.consistency else None,
            "integrations": dict(self.integrations),
            "observability": self.observability.to_dict() if self.observability else None,
            "metadata": public_meta,
            "error": self.error,
            "version": self.version,
        }
