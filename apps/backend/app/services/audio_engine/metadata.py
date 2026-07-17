"""AudioMetadata builder."""

from __future__ import annotations

from app.services.audio_engine.models import AudioMetadata, VoiceClip


def build_metadata(
    job_id: str,
    *,
    duration_sec: float,
    voice: list[VoiceClip],
    version: int = 1,
) -> AudioMetadata:
    languages = sorted({(c.language or "en").lower() for c in voice}) or ["en"]
    tags = ["rtas-audio", "phase4", "sprint1"]
    if any(c.character for c in voice):
        tags.append("dialogue")
    return AudioMetadata(
        job_id=job_id,
        sample_rate=48000,
        channels=2,
        bit_depth=24,
        loudness_lufs=-14.0,
        duration_sec=round(duration_sec, 3),
        languages=languages,
        tags=tags,
        version=version,
    )
