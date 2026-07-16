"""Export format matrix — MP4/MOV/WEBM × aspect × resolution × HDR."""

from __future__ import annotations

from typing import Any

from app.services.intelligence.production_render.models import (
    AspectRatio,
    ContainerFormat,
    ExportSpec,
    ResolutionTier,
)
from app.services.intelligence.models import PromptIntelligenceResult


def _default_aspect(understanding: dict[str, Any] | None, category: str) -> AspectRatio:
    cat = str((understanding or {}).get("category") or category or "").lower()
    if any(k in cat for k in ("tiktok", "shorts", "reel", "instagram")):
        return "vertical"
    if "podcast" in cat:
        return "landscape"
    return "landscape"


def _resolution_for(
    intelligence: PromptIntelligenceResult,
    *,
    prefer_4k: bool = False,
    eight_k_ready: bool = False,
) -> ResolutionTier:
    if eight_k_ready:
        return "8k_ready"
    if prefer_4k or intelligence.estimated_duration_seconds >= 45:
        return "4k"
    return "1080p"


def build_export_specs(
    intelligence: PromptIntelligenceResult,
    *,
    understanding: dict[str, Any] | None = None,
    include_all_aspects: bool = True,
) -> list[ExportSpec]:
    primary_aspect = _default_aspect(understanding, intelligence.category)
    primary_res = _resolution_for(intelligence)
    hdr = intelligence.cinematic_genre in ("narrative", "music_video") or (
        (understanding or {}).get("mood") in ("Epic", "Emotional")
    )

    formats: list[ContainerFormat] = ["mp4", "mov", "webm"]
    aspects: list[AspectRatio] = (
        ["vertical", "landscape", "square"] if include_all_aspects else [primary_aspect]
    )

    specs: list[ExportSpec] = []
    for fmt in formats:
        for aspect in aspects:
            res = primary_res
            # Shorts prefer 1080p vertical primary; keep 4k as optional landscape
            if aspect == "vertical" and res == "4k":
                res = "1080p"
            codec_v = "h264" if fmt != "webm" else "vp9"
            if res in ("4k", "8k_ready") and fmt == "mp4":
                codec_v = "h265"
            bitrate = {
                "720p": 8.0,
                "1080p": 16.0,
                "4k": 45.0,
                "8k_ready": 80.0,
            }[res]
            if aspect == "vertical":
                bitrate *= 0.85

            notes = [
                f"Primary aspect preference: {primary_aspect}",
                "Normalize loudness to -14 LUFS stereo",
            ]
            if res == "8k_ready":
                notes.append("Master timeline authored 8K-ready; deliver proxy 4K unless requested")
            if hdr and fmt in ("mp4", "mov"):
                notes.append("HDR10 metadata optional — SDR fallback required")

            specs.append(
                ExportSpec(
                    format=fmt,
                    aspect=aspect,
                    resolution=res,
                    hdr=bool(hdr and fmt != "webm"),
                    fps=24 if intelligence.category in ("story",) else 30,
                    audio_channels="stereo",
                    codec_video=codec_v,
                    codec_audio="aac" if fmt != "webm" else "opus",
                    bitrate_hint_mbps=round(bitrate, 1),
                    notes=notes,
                )
            )

    # Explicit 8K-ready master card (planning)
    specs.append(
        ExportSpec(
            format="mov",
            aspect=primary_aspect,
            resolution="8k_ready",
            hdr=True,
            fps=24,
            audio_channels="stereo",
            codec_video="prores_or_h265",
            codec_audio="pcm_or_aac",
            bitrate_hint_mbps=120.0,
            notes=[
                "Archive/master timeline — 8K ready composition",
                "Not required for social delivery",
            ],
        )
    )
    return specs


def primary_export_spec(specs: list[ExportSpec]) -> ExportSpec:
    # Prefer mp4 + default aspect + 1080p/4k
    for s in specs:
        if s.format == "mp4" and s.resolution in ("1080p", "4k") and s.aspect == "landscape":
            return s
    for s in specs:
        if s.format == "mp4":
            return s
    return specs[0]
