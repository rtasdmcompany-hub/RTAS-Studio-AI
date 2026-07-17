"""Audio/video packaging for multi-format export."""

from __future__ import annotations

import hashlib
from typing import Any

from app.services.audio_export.models import ExportAsset, ExportProfile


def _checksum(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]


def _size_estimate(
    profile: ExportProfile,
    *,
    duration_sec: float,
    quality: str,
    kind: str,
) -> int:
    duration = max(1.0, float(duration_sec))
    q_factor = {"low": 0.5, "medium": 0.75, "high": 1.0, "broadcast": 1.5}.get(quality, 1.0)
    if kind == "video":
        return int(profile.video_bitrate_kbps * 125 * duration * q_factor)
    if kind == "audio":
        return int(profile.audio_bitrate_kbps * 125 * duration * q_factor)
    if kind in ("subtitle", "caption"):
        return int(2048 + duration * 40)
    if kind == "thumbnail":
        return 180_000
    if kind == "metadata":
        return 4096
    return int(50_000 * duration * q_factor)


def build_package_assets(
    job_id: str,
    profile: ExportProfile,
    *,
    duration_sec: float = 8.0,
    quality: str = "high",
    watermark: bool = False,
    include_subtitles: bool = True,
    include_captions: bool = True,
    include_thumbnail: bool = True,
    extra_audio_formats: list[str] | None = None,
    timeline_summary: dict[str, Any] | None = None,
    localization_summary: dict[str, Any] | None = None,
) -> list[ExportAsset]:
    assets: list[ExportAsset] = []
    base = f"/media/export/{job_id}"

    video_url = f"{base}/master.{profile.video_format}"
    video_size = _size_estimate(profile, duration_sec=duration_sec, quality=quality, kind="video")
    assets.append(
        ExportAsset(
            asset_id=f"{job_id}_video",
            kind="video",
            format=profile.video_format,
            url=video_url,
            size_bytes=video_size,
            checksum=_checksum(job_id, "video", profile.video_format),
            mime_type=f"video/{profile.video_format}",
            verified=False,
            metadata={
                "resolution": profile.resolution,
                "codec": profile.video_codec,
                "bitrate_kbps": profile.video_bitrate_kbps,
                "watermark": watermark,
            },
        )
    )

    audio_formats = [profile.audio_format]
    for fmt in extra_audio_formats or []:
        if fmt not in audio_formats and fmt in ("wav", "mp3", "flac", "aac", "ogg"):
            audio_formats.append(fmt)

    for fmt in audio_formats:
        size = _size_estimate(profile, duration_sec=duration_sec, quality=quality, kind="audio")
        assets.append(
            ExportAsset(
                asset_id=f"{job_id}_audio_{fmt}",
                kind="audio",
                format=fmt,
                url=f"{base}/audio.{fmt}",
                size_bytes=size,
                checksum=_checksum(job_id, "audio", fmt),
                mime_type=f"audio/{fmt}",
                verified=False,
                metadata={
                    "loudness_lufs": profile.audio_loudness_lufs,
                    "bitrate_kbps": profile.audio_bitrate_kbps,
                    "codec": profile.audio_codec if fmt == profile.audio_format else fmt,
                },
            )
        )

    if include_subtitles:
        sub_url = None
        if isinstance(localization_summary, dict):
            sub_url = localization_summary.get("subtitle_url")
        assets.append(
            ExportAsset(
                asset_id=f"{job_id}_subs",
                kind="subtitle",
                format="vtt",
                url=sub_url or f"{base}/subs.vtt",
                size_bytes=_size_estimate(
                    profile, duration_sec=duration_sec, quality=quality, kind="subtitle"
                ),
                checksum=_checksum(job_id, "subtitle"),
                mime_type="text/vtt",
                verified=False,
            )
        )

    if include_captions:
        cap_url = None
        if isinstance(localization_summary, dict):
            cap_url = localization_summary.get("caption_url")
        assets.append(
            ExportAsset(
                asset_id=f"{job_id}_caps",
                kind="caption",
                format="vtt",
                url=cap_url or f"{base}/caps.vtt",
                size_bytes=_size_estimate(
                    profile, duration_sec=duration_sec, quality=quality, kind="caption"
                ),
                checksum=_checksum(job_id, "caption"),
                mime_type="text/vtt",
                verified=False,
            )
        )

    if include_thumbnail:
        assets.append(
            ExportAsset(
                asset_id=f"{job_id}_thumb",
                kind="thumbnail",
                format="jpg",
                url=f"{base}/thumb.jpg",
                size_bytes=_size_estimate(
                    profile, duration_sec=duration_sec, quality=quality, kind="thumbnail"
                ),
                checksum=_checksum(job_id, "thumbnail"),
                mime_type="image/jpeg",
                verified=False,
            )
        )

    meta_fmt = profile.metadata_format
    meta_payload_hint = {
        "platform": profile.platform,
        "resolution": profile.resolution,
        "timeline_job_id": (timeline_summary or {}).get("job_id"),
        "track_count": (timeline_summary or {}).get("track_count"),
        "loudness_lufs": profile.audio_loudness_lufs,
    }
    assets.append(
        ExportAsset(
            asset_id=f"{job_id}_meta",
            kind="metadata",
            format=meta_fmt,
            url=f"{base}/metadata.{meta_fmt}",
            size_bytes=_size_estimate(
                profile, duration_sec=duration_sec, quality=quality, kind="metadata"
            ),
            checksum=_checksum(job_id, "metadata", meta_fmt),
            mime_type="application/json" if meta_fmt == "json" else "application/xml",
            verified=False,
            metadata=meta_payload_hint,
        )
    )

    package_size = sum(a.size_bytes for a in assets)
    # Compression estimate (~12% for package zip)
    compressed = int(package_size * 0.88)
    assets.append(
        ExportAsset(
            asset_id=f"{job_id}_package",
            kind="package",
            format="zip",
            url=f"{base}/package.zip",
            size_bytes=compressed,
            checksum=_checksum(job_id, "package"),
            mime_type="application/zip",
            verified=False,
            metadata={"asset_count": len(assets), "uncompressed_bytes": package_size},
        )
    )
    return assets


def verify_assets(assets: list[ExportAsset]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    for a in assets:
        if not a.url or not a.checksum or a.size_bytes <= 0:
            errors.append(f"invalid asset: {a.asset_id}")
        else:
            a.verified = True
    return len(errors) == 0, errors
