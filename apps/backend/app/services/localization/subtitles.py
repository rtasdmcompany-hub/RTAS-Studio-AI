"""Subtitle / caption generation with timing."""

from __future__ import annotations

from app.services.localization.models import SubtitleCue, TranslationSegment


def build_subtitle_cues(
    segments: list[TranslationSegment],
    *,
    language: str,
    job_id: str,
    as_captions: bool = False,
) -> list[SubtitleCue]:
    cues: list[SubtitleCue] = []
    prefix = "cap" if as_captions else "sub"
    for i, seg in enumerate(segments):
        text = seg.translated_text
        if as_captions:
            text = text.upper() if language == "en" else text
        cues.append(
            SubtitleCue(
                cue_id=f"{prefix}_{job_id}_{i}",
                start_sec=seg.start_sec,
                end_sec=seg.end_sec,
                text=text,
                language=language,
                speaker_id=seg.speaker_id,
            )
        )
    return cues


def cues_to_vtt(cues: list[SubtitleCue]) -> str:
    lines = ["WEBVTT", ""]
    for c in cues:
        lines.append(f"{_ts(c.start_sec)} --> {_ts(c.end_sec)}")
        lines.append(c.text)
        lines.append("")
    return "\n".join(lines)


def _ts(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"
