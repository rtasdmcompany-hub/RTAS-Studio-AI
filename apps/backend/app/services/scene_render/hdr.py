"""HDR pipeline — exposure, tonemap, bloom."""

from __future__ import annotations

from typing import Any, Literal

from app.services.scene_render.models import HDRConfig, RenderQuality


def build_hdr(
    text: str,
    *,
    quality: RenderQuality,
    lighting_temp_k: int = 5600,
    visual_style: dict[str, Any] | None = None,
) -> HDRConfig:
    t = (text or "").lower()
    vs = visual_style or {}

    exposure = 0.0
    if any(x in t for x in ("night", "dark", "noir")):
        exposure = -0.6
    elif any(x in t for x in ("bright", "desert", "snow", "overexposed")):
        exposure = 0.4
    elif any(x in t for x in ("golden hour", "sunset")):
        exposure = -0.15

    tonemap: Literal["aces", "reinhard", "filmic"] = "aces"
    if "filmic" in str(vs.get("look") or "").lower() or "filmic" in t:
        tonemap = "filmic"

    bloom = 0.15
    if any(x in t for x in ("neon", "hdr", "bloom", "glow", "fire", "explosion")):
        bloom = 0.35 if quality in ("production", "cinema") else 0.25

    contrast = 1.05 if quality in ("production", "cinema") else 1.0

    return HDRConfig(
        enabled=True,
        exposure=round(exposure, 3),
        white_balance_k=int(lighting_temp_k),
        tonemapper=tonemap,
        bloom=round(bloom, 3),
        contrast=round(contrast, 3),
        notes=f"HDR10-ready path; tonemap={tonemap}",
    )
