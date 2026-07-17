"""Reflection configuration — SSR / probes / ray-traced ready."""

from __future__ import annotations

from typing import Literal

from app.services.scene_render.models import ReflectionConfig, RenderQuality


def build_reflections(
    text: str,
    *,
    quality: RenderQuality,
    ray_tracing_ready: bool,
) -> ReflectionConfig:
    t = (text or "").lower()
    glossy = any(
        x in t
        for x in ("glass", "mirror", "wet", "rain", "water", "metal", "chrome", "reflection")
    )

    mode: Literal["screen_space", "probe", "ray_traced", "hybrid"]
    if ray_tracing_ready and quality in ("production", "cinema"):
        mode = "hybrid" if glossy else "ray_traced"
    elif glossy:
        mode = "screen_space"
    else:
        mode = "probe"

    bounces = {"draft": 1, "preview": 1, "production": 2, "cinema": 3}[quality]
    intensity = 0.75 if glossy else 0.45

    return ReflectionConfig(
        enabled=True,
        mode=mode,
        intensity=intensity,
        roughness_cutoff=0.55 if glossy else 0.35,
        max_bounces=bounces,
        notes=f"reflection mode={mode}; glossy_surfaces={glossy}",
    )
