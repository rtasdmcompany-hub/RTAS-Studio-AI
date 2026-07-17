"""Speech Timing Engine — duration, pauses, transitions, overlap prevention."""

from __future__ import annotations

import re

from app.services.voice_intelligence.emotions import emotion_delivery_hints
from app.services.voice_intelligence.models import DialogueLine, TimingPlan
from app.services.voice_intelligence.version import WORDS_PER_MINUTE_BASE


def _word_count(text: str) -> int:
    words = re.findall(r"[A-Za-z0-9']+", text or "")
    return max(1, len(words))


def speaking_duration_sec(
    text: str,
    *,
    speaking_speed: float = 1.0,
    emotion: str = "calm",
) -> float:
    hints = emotion_delivery_hints(emotion)  # type: ignore[arg-type]
    pace = float(hints.get("pace_bias", 1.0))
    speed = max(0.5, min(1.5, float(speaking_speed))) * pace
    wpm = WORDS_PER_MINUTE_BASE * speed
    minutes = _word_count(text) / wpm
    return round(max(0.4, minutes * 60.0), 3)


def pause_after_sec(line: DialogueLine, *, next_line: DialogueLine | None) -> tuple[float, float, float]:
    """Return (pause_after, dramatic_pause, breathing_pause)."""
    dramatic = 0.0
    breathing = 0.18
    pause = 0.35

    if line.emotion in ("suspense", "fear", "serious"):
        dramatic = 0.55
        pause = 0.5
    elif line.emotion in ("sad", "emotional", "romantic"):
        dramatic = 0.35
        pause = 0.45
    elif line.emotion in ("excited", "angry"):
        pause = 0.22
        breathing = 0.12

    if line.text.rstrip().endswith("..."):
        dramatic = max(dramatic, 0.7)
    if line.is_narration or line.is_voice_over:
        pause = max(pause, 0.4)
    if line.is_internal:
        dramatic = max(dramatic, 0.4)
        breathing = 0.25
    if next_line and next_line.role != line.role:
        pause += 0.15  # speaker transition
    return round(pause, 3), round(dramatic, 3), round(breathing, 3)


def apply_timing(
    lines: list[DialogueLine],
    *,
    speaking_speeds: dict[str, float] | None = None,
) -> TimingPlan:
    speeds = speaking_speeds or {}
    cursor = 0.0
    total_speak = 0.0
    total_pause = 0.0
    total_dramatic = 0.0
    total_breathing = 0.0
    transition = 0.0
    timings: list[dict] = []
    prev_role = None

    for i, line in enumerate(lines):
        next_line = lines[i + 1] if i + 1 < len(lines) else None
        key = line.character_slot or line.role
        speed = float(speeds.get(key, speeds.get(line.role, 1.0)))
        speak = speaking_duration_sec(line.text, speaking_speed=speed, emotion=line.emotion)
        pause, dramatic, breathing = pause_after_sec(line, next_line=next_line)

        if prev_role is not None and prev_role != line.role:
            transition += 0.12
            cursor += 0.12

        start = cursor
        end = start + speak
        # Overlap prevention: never start before previous end
        if timings and start < timings[-1]["end_sec"]:
            start = timings[-1]["end_sec"]
            end = start + speak

        line.start_sec = round(start, 3)
        line.end_sec = round(end, 3)
        line.speaking_duration_sec = speak
        line.pause_after_sec = pause
        line.dramatic_pause_sec = dramatic
        line.breathing_pause_sec = breathing

        cursor = end + pause + dramatic + breathing
        total_speak += speak
        total_pause += pause
        total_dramatic += dramatic
        total_breathing += breathing
        prev_role = line.role

        timings.append(
            {
                "line_id": line.line_id,
                "start_sec": line.start_sec,
                "end_sec": line.end_sec,
                "speaking_duration_sec": speak,
                "pause_after_sec": pause,
                "dramatic_pause_sec": dramatic,
                "breathing_pause_sec": breathing,
            }
        )

    # Verify no overlaps
    overlap_prevented = True
    for i in range(1, len(timings)):
        if timings[i]["start_sec"] < timings[i - 1]["end_sec"] - 0.001:
            overlap_prevented = False
            timings[i]["start_sec"] = timings[i - 1]["end_sec"]
            timings[i]["end_sec"] = timings[i]["start_sec"] + timings[i]["speaking_duration_sec"]
            overlap_prevented = True

    total = cursor if lines else 0.0
    return TimingPlan(
        total_duration_sec=round(total, 3),
        speaking_duration_sec=round(total_speak, 3),
        pause_duration_sec=round(total_pause, 3),
        dramatic_pause_sec=round(total_dramatic, 3),
        breathing_pause_sec=round(total_breathing, 3),
        transition_timing_sec=round(transition, 3),
        overlap_prevented=overlap_prevented,
        line_timings=timings,
    )
