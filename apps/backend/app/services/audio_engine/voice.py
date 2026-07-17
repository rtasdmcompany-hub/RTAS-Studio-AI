"""VoiceService — voice clip planning from prompts / audio director."""

from __future__ import annotations

import hashlib
from typing import Any

from app.services.audio_engine.models import VoiceClip


def build_voice_clips(
    prompt: str,
    audio_director: dict[str, Any] | None = None,
) -> list[VoiceClip]:
    clips: list[VoiceClip] = []
    timeline = (audio_director or {}).get("voice_timeline") or []
    if isinstance(timeline, list) and timeline:
        for i, item in enumerate(timeline[:24]):
            if not isinstance(item, dict):
                continue
            text = str(item.get("text") or item.get("dialogue") or "").strip()
            if not text:
                continue
            start = float(item.get("start_sec") or item.get("start") or i * 2.0)
            end = float(item.get("end_sec") or item.get("end") or start + 2.0)
            clips.append(
                VoiceClip(
                    clip_id=_id("voice", text, i),
                    text=text[:500],
                    character=(item.get("character") or item.get("speaker")),
                    language=str(item.get("language") or "en"),
                    start_sec=start,
                    end_sec=max(end, start + 0.1),
                    provider_hint=str(item.get("provider") or "simulation"),
                )
            )
    if not clips and prompt.strip():
        clips.append(
            VoiceClip(
                clip_id=_id("voice", prompt, 0),
                text=prompt.strip()[:500],
                start_sec=0.0,
                end_sec=min(8.0, max(2.0, len(prompt.split()) * 0.35)),
                provider_hint="simulation",
            )
        )
    return clips


def _id(prefix: str, seed: str, index: int) -> str:
    digest = hashlib.sha1(f"{prefix}:{seed}:{index}".encode()).hexdigest()[:10]
    return f"{prefix}_{digest}"
