"""AmbientService — ambient beds / atmospheres."""

from __future__ import annotations

import hashlib
from typing import Any

from app.services.audio_engine.models import AmbientClip


def build_ambient_clips(
    prompt: str,
    audio_director: dict[str, Any] | None = None,
) -> list[AmbientClip]:
    clips: list[AmbientClip] = []
    timeline = (audio_director or {}).get("ambient_timeline") or []
    if isinstance(timeline, list) and timeline:
        for i, item in enumerate(timeline[:12]):
            if not isinstance(item, dict):
                continue
            label = str(item.get("label") or item.get("name") or "ambience").strip()
            start = float(item.get("start_sec") or item.get("start") or 0.0)
            end = float(item.get("end_sec") or item.get("end") or start + 10.0)
            clips.append(
                AmbientClip(
                    clip_id=_id("amb", label, i),
                    label=label[:80],
                    intensity=float(item.get("intensity") or 0.5),
                    start_sec=start,
                    end_sec=max(end, start + 0.5),
                )
            )
    if not clips:
        label = "room tone"
        lower = prompt.lower()
        if "rain" in lower:
            label = "rain ambience"
        elif "city" in lower or "street" in lower:
            label = "city ambience"
        elif "forest" in lower or "nature" in lower:
            label = "nature ambience"
        clips.append(
            AmbientClip(
                clip_id=_id("amb", label, 0),
                label=label,
                intensity=0.45,
                start_sec=0.0,
                end_sec=12.0,
            )
        )
    return clips


def _id(prefix: str, seed: str, index: int) -> str:
    digest = hashlib.sha1(f"{prefix}:{seed}:{index}".encode()).hexdigest()[:10]
    return f"{prefix}_{digest}"
