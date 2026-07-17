"""Ray-tracing readiness and quality tiers."""

from __future__ import annotations

from app.services.scene_render.models import RayTracingConfig, RenderQuality

_SAMPLES = {"draft": 1, "preview": 4, "production": 16, "cinema": 64}
_BOUNCES = {"draft": 1, "preview": 2, "production": 4, "cinema": 6}


def build_ray_tracing(
    text: str,
    *,
    quality: RenderQuality,
    force_ready: bool | None = None,
) -> RayTracingConfig:
    t = (text or "").lower()
    wants_rt = force_ready
    if wants_rt is None:
        wants_rt = quality in ("production", "cinema") or any(
            x in t
            for x in (
                "ray trac",
                "raytrac",
                "path trac",
                "glass",
                "mirror",
                "reflection",
                "gi ",
                "global illumination",
                "cinema",
            )
        )

    ready = bool(wants_rt)
    notes = [
        "Ray-tracing ready: materials, lights, and probes authored for RT path.",
        "Falls back to raster+SSR/probe when GPU RT unavailable.",
    ]
    if not ready:
        notes.append("Draft/preview raster path; RT flags prepared for upgrade.")

    return RayTracingConfig(
        ready=ready,
        quality=quality,
        samples_per_pixel=_SAMPLES[quality],
        max_bounces=_BOUNCES[quality],
        denoise=quality != "draft",
        reflections=ready,
        shadows=ready and quality in ("production", "cinema"),
        global_illumination=ready and quality == "cinema",
        notes=notes,
    )
