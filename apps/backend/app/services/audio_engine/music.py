"""MusicService — music bed planning."""

from __future__ import annotations

import hashlib
from typing import Any

from app.services.audio_engine.models import MusicClip


def build_music_clips(
    prompt: str,
    audio_director: dict[str, Any] | None = None,
) -> list[MusicClip]:
    clips: list[MusicClip] = []
    timeline = (audio_director or {}).get("music_timeline") or []
    if isinstance(timeline, list) and timeline:
        for i, item in enumerate(timeline[:12]):
            if not isinstance(item, dict):
                continue
            style = str(item.get("style") or item.get("genre") or "cinematic").strip()
            start = float(item.get("start_sec") or item.get("start") or 0.0)
            end = float(item.get("end_sec") or item.get("end") or start + 12.0)
            clips.append(
                MusicClip(
                    clip_id=_id("music", style, i),
                    style=style[:80],
                    mood=str(item.get("mood") or "neutral")[:40],
                    start_sec=start,
                    end_sec=max(end, start + 1.0),
                    loop=bool(item.get("loop", False)),
                    provider_hint=str(item.get("provider") or "simulation"),
                )
            )
    if not clips:
        mood = "cinematic"
        lower = prompt.lower()
        if "calm" in lower or "soft" in lower:
            mood = "calm"
        elif "action" in lower or "intense" in lower:
            mood = "intense"
        clips.append(
            MusicClip(
                clip_id=_id("music", mood, 0),
                style="cinematic underscore",
                mood=mood,
                start_sec=0.0,
                end_sec=12.0,
                loop=True,
            )
        )
    return clips


def _id(prefix: str, seed: str, index: int) -> str:
    digest = hashlib.sha1(f"{prefix}:{seed}:{index}".encode()).hexdigest()[:10]
    return f"{prefix}_{digest}"
