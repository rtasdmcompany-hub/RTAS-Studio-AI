"""Bridge parent voice/music/sfx/video into mix/master context."""

from __future__ import annotations

from typing import Any


def adapt_from_pipeline(
    *,
    voice_summary: dict[str, Any] | None = None,
    music_summary: dict[str, Any] | None = None,
    sfx_summary: dict[str, Any] | None = None,
    audio_engine_summary: dict[str, Any] | None = None,
    video_engine: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Collect parent IDs and hints for automatic pre-export mastering."""
    return {
        "parent_voice_job_id": (voice_summary or {}).get("job_id"),
        "parent_music_job_id": (music_summary or {}).get("job_id"),
        "parent_sfx_job_id": (sfx_summary or {}).get("job_id"),
        "parent_audio_job_id": (audio_engine_summary or {}).get("job_id"),
        "parent_video_job_id": (video_engine or {}).get("job_id"),
        "has_voice": bool(voice_summary),
        "has_music": bool(music_summary),
        "has_sfx": bool(sfx_summary),
        "music_energy": float((music_summary or {}).get("energy") or 0.5),
        "sfx_layers": int((sfx_summary or {}).get("layers") or 0),
    }
