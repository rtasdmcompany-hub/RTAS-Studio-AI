"""Avatar lip-sync frames from Audio Director cues or dialogue text."""

from __future__ import annotations

import re
from typing import Any

from app.services.talking_avatar.models import LipSyncFrame

_VISEME_RULES: tuple[tuple[re.Pattern[str], str, float], ...] = (
    (re.compile(r"[aeiou]", re.I), "AA", 0.75),
    (re.compile(r"[bpm]", re.I), "PP", 0.35),
    (re.compile(r"[fv]", re.I), "FF", 0.45),
    (re.compile(r"[l]", re.I), "L", 0.4),
    (re.compile(r"[w]", re.I), "OU", 0.55),
    (re.compile(r"[r]", re.I), "RR", 0.4),
    (re.compile(r"[sz]", re.I), "SS", 0.3),
    (re.compile(r"[tdn]", re.I), "DD", 0.35),
)


def _visemes_from_text(text: str) -> list[tuple[str, str, float]]:
    out: list[tuple[str, str, float]] = []
    tokens = re.findall(r"[A-Za-z\u0600-\u06FF']+", text or "")
    for token in tokens[:12]:
        viseme, openness = "REST", 0.15
        phoneme = token[:2].upper()
        for pattern, v, op in _VISEME_RULES:
            if pattern.search(token):
                viseme, openness = v, op
                break
        out.append((phoneme, viseme, openness))
    if not out:
        out.append(("SIL", "REST", 0.1))
    return out


def frames_from_audio_director(
    audio_director: dict[str, Any] | None,
    *,
    character_id: str,
) -> list[LipSyncFrame]:
    frames: list[LipSyncFrame] = []
    for cue in (audio_director or {}).get("lip_sync_timeline") or []:
        if not isinstance(cue, dict):
            continue
        openness = float(cue.get("mouth_openness") or 0.3)
        frames.append(
            LipSyncFrame(
                start_sec=float(cue.get("start_sec") or 0),
                end_sec=float(cue.get("end_sec") or 0.2),
                viseme=str(cue.get("viseme") or "REST"),
                phoneme_hint=str(cue.get("phoneme_hint") or "SIL"),
                mouth_openness=openness,
                jaw_drop=round(min(1.0, openness * 0.85), 3),
                dialogue_snippet=str(cue.get("dialogue_snippet") or ""),
                sync_confidence=float(cue.get("sync_confidence") or 0.8),
            )
        )
    return frames


def frames_from_dialogue(
    dialogue: str,
    *,
    start_sec: float = 0.0,
    duration_seconds: float = 8.0,
) -> list[LipSyncFrame]:
    visemes = _visemes_from_text(dialogue)
    slot = max(0.08, duration_seconds / max(1, len(visemes)))
    t = start_sec
    frames: list[LipSyncFrame] = []
    for phoneme, viseme, openness in visemes:
        frames.append(
            LipSyncFrame(
                start_sec=round(t, 3),
                end_sec=round(t + slot, 3),
                viseme=viseme,
                phoneme_hint=phoneme,
                mouth_openness=openness,
                jaw_drop=round(min(1.0, openness * 0.85), 3),
                dialogue_snippet=dialogue[:80],
                sync_confidence=0.82,
            )
        )
        t += slot
    return frames


def build_lip_sync_frames(
    *,
    audio_director: dict[str, Any] | None,
    character_id: str,
    dialogue: str | None,
    runtime_seconds: float,
) -> list[LipSyncFrame]:
    frames = frames_from_audio_director(audio_director, character_id=character_id)
    if frames:
        return frames
    text = (dialogue or "").strip() or "Hello, welcome."
    return frames_from_dialogue(text, start_sec=0.2, duration_seconds=max(2.0, runtime_seconds * 0.7))
