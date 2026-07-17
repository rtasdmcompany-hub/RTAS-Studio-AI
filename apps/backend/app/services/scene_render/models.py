"""Scene Render Engine — dataclasses."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

RenderQuality = Literal["draft", "preview", "production", "cinema"]
GpuJobState = Literal["queued", "running", "completed", "failed", "cancelled"]


@dataclass
class LightingSetup:
    key: str
    fill: str
    rim: str
    ambient: str
    practicals: list[str]
    color_temperature_k: int
    intensity: float
    volumetric: bool
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ShadowConfig:
    enabled: bool
    soft: bool
    contact_shadows: bool
    cascade_count: int
    bias: float
    intensity: float
    resolution: int
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ReflectionConfig:
    enabled: bool
    mode: Literal["screen_space", "probe", "ray_traced", "hybrid"]
    intensity: float
    roughness_cutoff: float
    max_bounces: int
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HDRConfig:
    enabled: bool
    exposure: float
    white_balance_k: int
    tonemapper: Literal["aces", "reinhard", "filmic"]
    bloom: float
    contrast: float
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RayTracingConfig:
    ready: bool
    quality: RenderQuality
    samples_per_pixel: int
    max_bounces: int
    denoise: bool
    reflections: bool
    shadows: bool
    global_illumination: bool
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MemoryBudget:
    target_vram_mb: int
    texture_budget_mb: int
    geometry_budget_mb: int
    particle_budget_mb: int
    cache_budget_mb: int
    streaming: bool
    texture_mip_bias: float
    instance_culling: bool
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SceneCacheEntry:
    cache_key: str
    scene_index: int
    fingerprint: str
    hits: int
    size_estimate_mb: float
    assets: list[str]
    stale: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GpuRenderJob:
    job_id: str
    scene_index: int
    priority: int
    state: GpuJobState
    quality: RenderQuality
    estimated_vram_mb: int
    estimated_ms: int
    dependencies: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SceneRenderPass:
    scene_index: int
    title: str
    duration_seconds: float
    lighting: LightingSetup
    shadows: ShadowConfig
    reflections: ReflectionConfig
    hdr: HDRConfig
    ray_tracing: RayTracingConfig
    cache: SceneCacheEntry
    memory: MemoryBudget
    gpu_job: GpuRenderJob
    directives: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scene_index": self.scene_index,
            "title": self.title,
            "duration_seconds": self.duration_seconds,
            "lighting": self.lighting.to_dict(),
            "shadows": self.shadows.to_dict(),
            "reflections": self.reflections.to_dict(),
            "hdr": self.hdr.to_dict(),
            "ray_tracing": self.ray_tracing.to_dict(),
            "cache": self.cache.to_dict(),
            "memory": self.memory.to_dict(),
            "gpu_job": self.gpu_job.to_dict(),
            "directives": self.directives,
        }


@dataclass
class SceneRenderPlan:
    job_id: str
    prompt: str
    quality: RenderQuality
    total_duration_seconds: float
    scenes: list[SceneRenderPass]
    gpu_queue: list[GpuRenderJob]
    scene_cache: list[SceneCacheEntry]
    memory_optimization: dict[str, Any]
    ray_tracing_ready: bool
    hdr_enabled: bool
    timeline: list[dict[str, Any]] = field(default_factory=list)
    director_integration: dict[str, Any] = field(default_factory=dict)
    production_integration: dict[str, Any] = field(default_factory=dict)
    physics_integration: dict[str, Any] = field(default_factory=dict)
    camera_integration: dict[str, Any] = field(default_factory=dict)
    provider_directives: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "prompt": self.prompt,
            "quality": self.quality,
            "total_duration_seconds": self.total_duration_seconds,
            "scenes": [s.to_dict() for s in self.scenes],
            "gpu_queue": [j.to_dict() for j in self.gpu_queue],
            "scene_cache": [c.to_dict() for c in self.scene_cache],
            "memory_optimization": self.memory_optimization,
            "ray_tracing_ready": self.ray_tracing_ready,
            "hdr_enabled": self.hdr_enabled,
            "timeline": self.timeline,
            "director_integration": self.director_integration,
            "production_integration": self.production_integration,
            "physics_integration": self.physics_integration,
            "camera_integration": self.camera_integration,
            "provider_directives": self.provider_directives,
        }

    def summary(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "scenes": len(self.scenes),
            "quality": self.quality,
            "total_duration_seconds": self.total_duration_seconds,
            "ray_tracing_ready": self.ray_tracing_ready,
            "hdr_enabled": self.hdr_enabled,
            "gpu_jobs": len(self.gpu_queue),
            "cache_entries": len(self.scene_cache),
            "vram_target_mb": (self.memory_optimization or {}).get("target_vram_mb"),
            "directives": self.provider_directives[:12],
        }
