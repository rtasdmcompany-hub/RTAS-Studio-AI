"""Download / delivery package readiness."""

from __future__ import annotations

import hashlib
from typing import Any

from app.services.video_engine.models import DownloadPackage


def build_download_package(
    *,
    prompt: str,
    production_render: dict[str, Any] | None,
    job_id: str,
    quality_overall: float,
    export_validated: bool,
) -> DownloadPackage:
    pr = production_render or {}
    specs = pr.get("export_specs") or []
    formats: list[str] = []
    for s in specs:
        if isinstance(s, dict) and s.get("format"):
            formats.append(str(s["format"]).lower())
    if not formats:
        formats = ["mp4", "mov", "webm"]

    ready = bool(export_validated) and quality_overall >= 0.7
    seed = f"{job_id}|{prompt[:80]}"
    checksum = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16]
    runtime = 0.0
    manifest = pr.get("video_manifest") or {}
    if isinstance(manifest, dict):
        try:
            runtime = float(manifest.get("runtime_seconds") or 0)
        except (TypeError, ValueError):
            runtime = 0.0
    # Rough bitrate estimate ~8 Mbps → MB
    size_mb = round(max(8.0, runtime * 8.0 / 8.0), 2) if runtime else 24.0

    filename = f"rtas_video_{job_id[-8:]}.mp4"
    notes = [
        "Primary delivery: MP4 H.264/H.265 with stereo mix.",
        "Alternate containers: MOV / WebM when export specs include them.",
    ]
    if ready:
        notes.append("Download package READY for client delivery.")
    else:
        notes.append("Download gated until export validation + quality threshold.")

    return DownloadPackage(
        ready=ready,
        formats=formats[:6],
        primary_url_hint=f"/api/video-engine/download/{job_id}",
        filename=filename,
        checksum_hint=f"sha1:{checksum}",
        size_estimate_mb=size_mb,
        expires_hint="72h",
        notes=notes,
    )
