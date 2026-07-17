"""Shadow configuration for scene rendering."""

from __future__ import annotations

from app.services.scene_render.models import RenderQuality, ShadowConfig


def build_shadows(
    text: str,
    *,
    quality: RenderQuality,
    hard_light: bool = False,
) -> ShadowConfig:
    t = (text or "").lower()
    soft = not hard_light and not any(x in t for x in ("harsh", "hard sun", "noon"))
    if any(x in t for x in ("soft", "overcast", "diffuse")):
        soft = True

    cascade = {"draft": 2, "preview": 3, "production": 4, "cinema": 4}[quality]
    resolution = {"draft": 1024, "preview": 2048, "production": 4096, "cinema": 4096}[
        quality
    ]
    intensity = 0.85 if soft else 0.95
    bias = 0.002 if soft else 0.0015

    return ShadowConfig(
        enabled=True,
        soft=soft,
        contact_shadows=quality in ("production", "cinema"),
        cascade_count=cascade,
        bias=bias,
        intensity=intensity,
        resolution=resolution,
        notes="PCF soft shadows" if soft else "crisp directional shadows",
    )
