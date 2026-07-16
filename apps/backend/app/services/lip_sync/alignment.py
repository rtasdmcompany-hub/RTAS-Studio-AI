"""Speech alignment — map dialogue onto a timed speech window."""

from __future__ import annotations

import re
from typing import Any

from app.services.lip_sync.models import SpeechAlignment, SupportedLanguage


def _word_tokens(text: str, language: SupportedLanguage) -> list[str]:
    if language in ("ur", "ar"):
        return re.findall(r"[\u0600-\u06FF]+|[A-Za-z']+", text or "")
    if language == "hi":
        return re.findall(r"[\u0900-\u097F]+|[A-Za-z']+", text or "")
    if language == "pa":
        return re.findall(r"[\u0A00-\u0A7F]+|[\u0600-\u06FF]+|[A-Za-z']+", text or "")
    return re.findall(r"[A-Za-z']+", text or "")


def align_speech(
    dialogue: str,
    language: SupportedLanguage,
    *,
    start_sec: float = 0.0,
    duration_seconds: float | None = None,
    voice_timeline: list[dict[str, Any]] | None = None,
) -> SpeechAlignment:
    """
    Align dialogue words into a timed window.

    Prefer voice timeline bounds when provided (Audio Director integration).
    """
    speech_start = start_sec
    speech_end = start_sec + (duration_seconds or 0)

    if voice_timeline:
        starts = [float(c.get("start_sec") or 0) for c in voice_timeline if isinstance(c, dict)]
        ends = [float(c.get("end_sec") or 0) for c in voice_timeline if isinstance(c, dict)]
        if starts and ends:
            speech_start = min(starts)
            speech_end = max(ends)

    if speech_end <= speech_start:
        # Estimate from word count (~2.8 wps conversational)
        words_est = max(1, len(_word_tokens(dialogue, language)))
        speech_end = speech_start + max(1.5, words_est / 2.8)

    words_raw = _word_tokens(dialogue, language)
    span = max(0.05, speech_end - speech_start)
    slot = span / max(1, len(words_raw))
    words: list[dict[str, Any]] = []
    t = speech_start
    for i, w in enumerate(words_raw):
        words.append(
            {
                "index": i,
                "word": w,
                "start_sec": round(t, 3),
                "end_sec": round(t + slot, 3),
            }
        )
        t += slot

    # Pause windows: gaps after punctuation / short silences every ~4 words
    pauses: list[dict[str, Any]] = []
    for i, w in enumerate(words):
        if (i + 1) % 4 == 0 and i < len(words) - 1:
            pauses.append(
                {
                    "start_sec": w["end_sec"],
                    "end_sec": round(min(speech_end, w["end_sec"] + 0.12), 3),
                    "kind": "micro_pause",
                }
            )

    wps = len(words_raw) / span if span > 0 else 0.0
    return SpeechAlignment(
        language=language,
        speech_start_sec=round(speech_start, 3),
        speech_end_sec=round(speech_end, 3),
        duration_seconds=round(span, 3),
        words=words,
        pause_windows=pauses,
        words_per_second=round(wps, 3),
    )
