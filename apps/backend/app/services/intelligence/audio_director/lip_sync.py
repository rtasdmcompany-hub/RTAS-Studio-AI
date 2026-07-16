"""Lip Sync Timeline — delegates to Professional Lip Sync Engine."""

from __future__ import annotations

import re
from typing import Any

from app.services.intelligence.audio_director.models import (
    AudioDetection,
    LipSyncCue,
    TimelineCue,
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
    words = re.findall(r"[A-Za-z\u0600-\u06FF']+", prompt or "")
    if len(words) >= 6:
        return " ".join(words[:8])
    return "…"


def build_lip_sync_timeline(
    detection: AudioDetection,
    voice_timeline: list[TimelineCue],
    *,
    prompt: str,
    character_id: str,
    scenes: list[Any] | None = None,
) -> list[LipSyncCue]:
    """
    Build lip-sync cues aligned to voice timeline via Professional Lip Sync Engine.
    """
    if detection.category == "music_video" and not detection.has_dialogue:
        pass
    elif not (detection.has_narration or detection.has_dialogue or detection.has_singing):
        return []

    syncable = [
        c for c in voice_timeline if c.kind in ("dialogue", "vocals", "narration")
    ]
    if not syncable:
        return []

    scene_titles = {
        getattr(s, "index", i): getattr(s, "title", f"Scene {i}")
        for i, s in enumerate(scenes or [])
    }

    try:
        from app.services.lip_sync import build_lip_sync_plan
    except Exception:
        build_lip_sync_plan = None  # type: ignore[assignment]

    cues: list[LipSyncCue] = []
    for voice_cue in syncable:
        scene_index = (voice_cue.metadata or {}).get("scene_index")
        title = str(scene_titles.get(scene_index, voice_cue.label))
        snippet = _snippet_for_scene(title, prompt, detection.emotion)
        base_conf = 0.55 if voice_cue.kind == "narration" else 0.82

        if build_lip_sync_plan is not None:
            plan = build_lip_sync_plan(
                snippet,
                language_hint=detection.language,
                emotion_hint=detection.emotion,
                start_sec=voice_cue.start_sec,
                duration_seconds=max(0.2, voice_cue.end_sec - voice_cue.start_sec),
                character_id=character_id,
                voice_timeline=[
                    {
                        "start_sec": voice_cue.start_sec,
                        "end_sec": voice_cue.end_sec,
                        "kind": voice_cue.kind,
                    }
                ],
            )
            for v in plan.visemes:
                cues.append(
                    LipSyncCue(
                        start_sec=round(v.start_sec, 2),
                        end_sec=round(v.end_sec, 2),
                        character_id=character_id,
                        phoneme_hint=v.phoneme,
                        mouth_openness=v.mouth_openness,
                        viseme=v.viseme,
                        dialogue_snippet=snippet,
                        sync_confidence=min(base_conf + 0.05, v.sync_confidence),
                    )
                )
            continue

        # Fallback (should rarely run)
        cues.append(
            LipSyncCue(
                start_sec=round(voice_cue.start_sec, 2),
                end_sec=round(voice_cue.end_sec, 2),
                character_id=character_id,
                phoneme_hint="AA",
                mouth_openness=0.5,
                viseme="AA",
                dialogue_snippet=snippet,
                sync_confidence=base_conf,
            )
        )
    return cues
