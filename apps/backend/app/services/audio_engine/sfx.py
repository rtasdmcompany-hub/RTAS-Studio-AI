"""SFXService — sound effects planning."""

from __future__ import annotations

import hashlib
from typing import Any

from app.services.audio_engine.models import SfxClip


def build_sfx_clips(
    prompt: str,
    audio_director: dict[str, Any] | None = None,
) -> list[SfxClip]:
    clips: list[SfxClip] = []
    timeline = (audio_director or {}).get("sfx_timeline") or []
    if isinstance(timeline, list) and timeline:
        for i, item in enumerate(timeline[:32]):
            if not isinstance(item, dict):
                continue
            label = str(item.get("label") or item.get("name") or "sfx").strip()
            start = float(item.get("start_sec") or item.get("start") or float(i))
            dur = float(item.get("duration_sec") or item.get("duration") or 0.5)
            clips.append(
                SfxClip(
                    clip_id=_id("sfx", label, i),
                    label=label[:80],
                    category=str(item.get("category") or "foley")[:40],
                    start_sec=start,
                    duration_sec=max(0.05, dur),
                )
            )
    if not clips:
        lower = prompt.lower()
        guesses = []
        if "door" in lower:
            guesses.append(("door open", "foley"))
        if "footstep" in lower or "walk" in lower:
            guesses.append(("footsteps", "foley"))
        if "whoosh" in lower or "transition" in lower:
            guesses.append(("whoosh", "transition"))
        if not guesses:
            guesses.append(("soft accent", "foley"))
        for i, (label, cat) in enumerate(guesses[:6]):
            clips.append(
                SfxClip(
                    clip_id=_id("sfx", label, i),
                    label=label,
                    category=cat,
                    start_sec=float(i * 2),
                    duration_sec=0.4,
                )
            )
    return clips


def _id(prefix: str, seed: str, index: int) -> str:
    digest = hashlib.sha1(f"{prefix}:{seed}:{index}".encode()).hexdigest()[:10]
    return f"{prefix}_{digest}"
