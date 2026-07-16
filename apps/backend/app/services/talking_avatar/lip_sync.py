"""Avatar lip-sync frames — prefers Professional Lip Sync Engine."""

from __future__ import annotations

from typing import Any

from app.services.talking_avatar.models import LipSyncFrame


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
    language_hint: str | None = None,
    emotion_hint: str | None = None,
) -> list[LipSyncFrame]:
    try:
        from app.services.lip_sync import build_lip_sync_plan

        plan = build_lip_sync_plan(
            dialogue,
            language_hint=language_hint,
            emotion_hint=emotion_hint,
            start_sec=start_sec,
            duration_seconds=duration_seconds,
        )
        return [
            LipSyncFrame(
                start_sec=v.start_sec,
                end_sec=v.end_sec,
                viseme=v.viseme,
                phoneme_hint=v.phoneme,
                mouth_openness=v.mouth_openness,
                jaw_drop=v.jaw_drop,
                dialogue_snippet=v.dialogue_snippet,
                sync_confidence=v.sync_confidence,
            )
            for v in plan.visemes
        ]
    except Exception:
        return [
            LipSyncFrame(
                start_sec=start_sec,
                end_sec=start_sec + duration_seconds,
                viseme="AA",
                phoneme_hint="AA",
                mouth_openness=0.5,
                jaw_drop=0.4,
                dialogue_snippet=(dialogue or "")[:80],
                sync_confidence=0.7,
            )
        ]


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
    lang = None
    emotion = None
    det = (audio_director or {}).get("detection") or {}
    if isinstance(det, dict):
        lang = det.get("language")
        emotion = det.get("emotion")
    return frames_from_dialogue(
        text,
        start_sec=0.2,
        duration_seconds=max(2.0, runtime_seconds * 0.7),
        language_hint=str(lang) if lang else None,
        emotion_hint=str(emotion) if emotion else None,
    )
