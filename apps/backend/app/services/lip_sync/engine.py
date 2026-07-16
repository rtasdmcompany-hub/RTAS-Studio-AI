"""
Professional Lip Sync Engine.

Multi-language phoneme detection, viseme mapping, speech alignment,
emotion sync, and production timeline output.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any
from uuid import uuid4

from app.services.lip_sync.alignment import align_speech
from app.services.lip_sync.emotion_sync import apply_emotion_to_visemes, resolve_emotion
from app.services.lip_sync.languages import detect_all_languages, detect_language
from app.services.lip_sync.models import LipSyncPlan, SupportedLanguage
from app.services.lip_sync.phonemes import detect_phonemes
from app.services.lip_sync.visemes import phonemes_to_visemes

logger = logging.getLogger(__name__)

_JOBS: dict[str, LipSyncPlan] = {}


def _job_id(dialogue: str) -> str:
    seed = f"{dialogue}|{uuid4().hex[:8]}"
    return f"lipsync_{hashlib.sha1(seed.encode('utf-8')).hexdigest()[:10]}"


def build_lip_sync_plan(
    dialogue: str,
    *,
    language_hint: str | None = None,
    emotion_hint: str | None = None,
    duration_seconds: float | None = None,
    start_sec: float = 0.0,
    character_id: str | None = None,
    audio_director: dict[str, Any] | None = None,
    voice_timeline: list[dict[str, Any]] | None = None,
) -> LipSyncPlan:
    text = (dialogue or "").strip()
    if not text and audio_director:
        # Pull from first lip/voice cue snippet
        for cue in audio_director.get("lip_sync_timeline") or []:
            if isinstance(cue, dict) and cue.get("dialogue_snippet"):
                text = str(cue["dialogue_snippet"])
                break
        if not text:
            for cue in audio_director.get("voice_timeline") or []:
                if isinstance(cue, dict) and cue.get("label"):
                    text = str(cue["label"])
                    break
    if not text:
        text = "Hello."

    language: SupportedLanguage = detect_language(
        text, hint=language_hint, audio_director=audio_director
    )
    languages = detect_all_languages(text)
    emotion, intensity = resolve_emotion(
        emotion_hint=emotion_hint,
        audio_director=audio_director,
        dialogue=text,
    )

    voice_tl = voice_timeline
    if voice_tl is None and audio_director:
        voice_tl = list(audio_director.get("voice_timeline") or [])

    alignment = align_speech(
        text,
        language,
        start_sec=start_sec,
        duration_seconds=duration_seconds,
        voice_timeline=voice_tl,
    )
    phonemes = detect_phonemes(
        text,
        language,
        start_sec=alignment.speech_start_sec,
        end_sec=alignment.speech_end_sec,
    )
    visemes = phonemes_to_visemes(
        phonemes,
        emotion=emotion,
        emotion_intensity=intensity,
        dialogue=text,
    )
    visemes = apply_emotion_to_visemes(visemes, emotion, intensity)

    timeline = [
        {
            "t": v.start_sec,
            "end": v.end_sec,
            "viseme": v.viseme,
            "phoneme": v.phoneme,
            "open": v.mouth_openness,
            "emotion": v.emotion,
        }
        for v in visemes
    ]

    plan = LipSyncPlan(
        job_id=_job_id(text),
        language=language,
        languages_detected=languages,
        emotion=emotion,
        alignment=alignment,
        phonemes=phonemes,
        visemes=visemes,
        timeline=timeline,
        dialogue=text,
        character_id=character_id,
        metadata={
            "engine": "lip_sync",
            "version": "1.0",
            "supported_languages": ["en", "ur", "ar", "hi", "pa"],
            "emotion_intensity": intensity,
        },
    )
    _JOBS[plan.job_id] = plan
    logger.info(
        "lip_sync language=%s phonemes=%s visemes=%s emotion=%s duration=%.2f",
        language,
        len(phonemes),
        len(visemes),
        emotion,
        alignment.duration_seconds,
    )
    return plan


def get_plan(job_id: str) -> LipSyncPlan | None:
    return _JOBS.get(job_id)


def build_lip_sync_dict(dialogue: str, **kwargs: Any) -> dict[str, Any]:
    plan = build_lip_sync_plan(dialogue, **kwargs)
    return {
        "plan": plan.to_dict(),
        "summary": plan.summary(),
        "timeline": plan.timeline,
        "audioDirectorCues": plan.to_audio_director_cues(),
    }
