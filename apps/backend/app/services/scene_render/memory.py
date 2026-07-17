"""Memory optimization budgets for scene rendering."""

from __future__ import annotations

from typing import Any

from app.services.scene_render.models import MemoryBudget, RenderQuality

_VRAM = {
    "draft": 2048,
    "preview": 4096,
    "production": 8192,
    "cinema": 12288,
}


def build_memory_budget(
    *,
    quality: RenderQuality,
    scene_count: int,
    particle_heavy: bool = False,
    physics_effects: list[str] | None = None,
) -> MemoryBudget:
    vram = _VRAM[quality]
    # Leave headroom for OS / compositor
    usable = int(vram * 0.82)
    tex = int(usable * 0.45)
    geo = int(usable * 0.25)
    particles = int(usable * (0.18 if particle_heavy else 0.08))
    cache = int(usable * 0.12)

    effects = set(physics_effects or [])
    mip_bias = 0.0 if quality in ("production", "cinema") else 0.5
    if "explosion" in effects or "fire" in effects:
        particles = int(particles * 1.3)
        mip_bias = max(0.0, mip_bias - 0.25)

    notes = [
        f"Target VRAM ~{vram}MB (usable {usable}MB) for quality={quality}.",
        "Stream large textures; prefer atlas + mipmaps.",
        "Instance-cull offscreen characters and props.",
    ]
    if scene_count > 3:
        notes.append("Reuse shared environment light probes across scenes.")
    if particle_heavy:
        notes.append("Cap particle overdraw; LOD distant emitters.")

    return MemoryBudget(
        target_vram_mb=vram,
        texture_budget_mb=tex,
        geometry_budget_mb=geo,
        particle_budget_mb=particles,
        cache_budget_mb=cache,
        streaming=True,
        texture_mip_bias=mip_bias,
        instance_culling=True,
        notes=notes,
    )


def optimize_memory_plan(
    budgets: list[MemoryBudget],
    *,
    quality: RenderQuality,
) -> dict[str, Any]:
    if not budgets:
        b = build_memory_budget(quality=quality, scene_count=1)
        budgets = [b]
    target = max(b.target_vram_mb for b in budgets)
    return {
        "target_vram_mb": target,
        "texture_budget_mb": max(b.texture_budget_mb for b in budgets),
        "geometry_budget_mb": max(b.geometry_budget_mb for b in budgets),
        "particle_budget_mb": max(b.particle_budget_mb for b in budgets),
        "cache_budget_mb": max(b.cache_budget_mb for b in budgets),
        "streaming": True,
        "instance_culling": True,
        "strategies": [
            "LRU scene cache eviction under pressure",
            "Texture streaming with mip bias",
            "GPU job serialization when VRAM headroom < 15%",
            "Share light probes / reflection probes across similar scenes",
        ],
        "per_scene": [b.to_dict() for b in budgets],
    }
