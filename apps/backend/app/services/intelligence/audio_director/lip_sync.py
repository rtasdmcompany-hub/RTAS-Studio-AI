"""Lip Sync Timeline planner (viseme / phoneme hints — planning only)."""

from __future__ import annotations

import re
from typing import Any

from app.services.intelligence.audio_director.models import (
    AudioDetection,
    LipSyncCue,
    TimelineCue,
)

# Simple grapheme → viseme mapping for planning cues
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


def _snippet_for_scene(title: str, prompt: str, emotion: str) -> str:
    title_l = title.lower()
    if "flashback" in title_l or "memory" in title_l:
        return "I still remember…"
    if "close" in title_l or "face" in title_l:
        if emotion in ("somber", "sad"):
            return "Why did you leave?"
        return "Look at me."
    if "walking" in title_l or "walk" in title_l:
        return "Every step feels heavier."
    if "ending" in title_l or "resolve" in title_l:
        return "Some loves never fade."
    # Fall back to short prompt slice
    words = re.findall(r"[A-Za-z\u0600-\u06FF']+", prompt or "")
    if len(words) >= 6:
        return " ".join(words[:8])
    return "…"


def _visemes_from_text(text: str) -> list[tuple[str, str, float]]:
    """Return list of (phoneme_hint, viseme, openness)."""
    out: list[tuple[str, str, float]] = []
    tokens = re.findall(r"[A-Za-z\u0600-\u06FF']+", text)
    for token in tokens[:8]:
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


def build_lip_sync_timeline(
    detection: AudioDetection,
    voice_timeline: list[TimelineCue],
    *,
    prompt: str,
    character_id: str,
    scenes: list[Any] | None = None,
) -> list[LipSyncCue]:
    """
    Build lip-sync cues aligned to voice timeline.

    Planning only — does not render audio/video. Suitable for talking-avatar /
    dialogue shots and character close-ups.
    """
    if detection.category == "music_video" and not detection.has_dialogue:
        # Singing still needs mouth sync on performance close-ups
        pass
    elif not (detection.has_narration or detection.has_dialogue or detection.has_singing):
        return []

    # Prefer syncing when we have a visible speaking character
    syncable = [
        c
        for c in voice_timeline
        if c.kind in ("dialogue", "vocals", "narration")
    ]
    if not syncable:
        return []

    cues: list[LipSyncCue] = []
    scene_titles = {
        getattr(s, "index", i): getattr(s, "title", f"Scene {i}")
        for i, s in enumerate(scenes or [])
    }

    for voice_cue in syncable:
        scene_index = (voice_cue.metadata or {}).get("scene_index")
        title = str(scene_titles.get(scene_index, voice_cue.label))
        # Narration may be off-camera — still plan sync for avatar / on-camera VO
        if voice_cue.kind == "narration" and detection.category in (
            "documentary",
            "advertisement",
        ):
            # Lower confidence off-camera narration
            base_conf = 0.55
        else:
            base_conf = 0.82

        snippet = _snippet_for_scene(title, prompt, detection.emotion)
        visemes = _visemes_from_text(snippet)
        dur = max(0.2, voice_cue.end_sec - voice_cue.start_sec)
        slot = dur / max(1, len(visemes))
        t = voice_cue.start_sec
        for phoneme, viseme, openness in visemes:
            cues.append(
                LipSyncCue(
                    start_sec=round(t, 2),
                    end_sec=round(t + slot, 2),
                    character_id=character_id,
                    phoneme_hint=phoneme,
                    mouth_openness=openness,
                    viseme=viseme,
                    dialogue_snippet=snippet,
                    sync_confidence=base_conf,
                )
            )
            t += slot
    return cues
