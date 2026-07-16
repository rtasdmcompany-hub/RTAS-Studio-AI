"""Captions / subtitles generation (SRT) from audio + scene plans."""

from __future__ import annotations

from typing import Any

from app.services.intelligence.production_render.models import SubtitleCue


def _fmt_ts(seconds: float) -> str:
    ms = int(round(max(0.0, seconds) * 1000))
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, milli = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{milli:03d}"


def build_captions(
    *,
    scenes: list[dict[str, Any]],
    audio_director: dict[str, Any] | None,
    prompt: str,
) -> list[SubtitleCue]:
    cues: list[SubtitleCue] = []
    voice_tl = list((audio_director or {}).get("voice_timeline") or [])
    lip_tl = list((audio_director or {}).get("lip_sync_timeline") or [])

    if voice_tl:
        for i, cue in enumerate(voice_tl, start=1):
            text = str(cue.get("label") or "…")
            # Prefer lip-sync dialogue snippet when overlapping
            for lip in lip_tl:
                if abs(float(lip.get("start_sec", -1)) - float(cue.get("start_sec", -2))) < 0.5:
                    text = str(lip.get("dialogue_snippet") or text)
                    break
            # Clean VO labels
            if text.startswith("VO —"):
                text = text.replace("VO —", "").strip()
            cues.append(
                SubtitleCue(
                    index=i,
                    start_sec=float(cue.get("start_sec") or 0),
                    end_sec=float(cue.get("end_sec") or 0),
                    text=text[:120],
                )
            )
        return cues

    # Fallback: one caption per scene
    t = 0.0
    for i, scene in enumerate(scenes, start=1):
        dur = float(scene.get("duration_seconds") or scene.get("estimated_duration_seconds") or 3)
        title = str(scene.get("title") or scene.get("scene_purpose") or f"Scene {i}")
        cues.append(
            SubtitleCue(
                index=i,
                start_sec=t,
                end_sec=t + dur,
                text=title[:120],
            )
        )
        t += dur
    if not cues and prompt:
        cues.append(SubtitleCue(index=1, start_sec=0.0, end_sec=3.0, text=prompt[:80]))
    return cues


def render_srt(captions: list[SubtitleCue]) -> str:
    blocks: list[str] = []
    for cue in captions:
        blocks.append(
            f"{cue.index}\n{_fmt_ts(cue.start_sec)} --> {_fmt_ts(cue.end_sec)}\n{cue.text}\n"
        )
    return "\n".join(blocks).strip() + ("\n" if blocks else "")
