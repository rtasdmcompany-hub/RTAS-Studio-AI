"""Duration estimation + voice quality scoring."""

from __future__ import annotations

from app.services.voice_generation.models import VoiceControls, VoiceQuality


def estimate_duration_sec(text: str, controls: VoiceControls) -> float:
    words = [w for w in text.strip().split() if w]
    # ~2.5 words/sec baseline; speed scales speaking rate
    speed = max(0.5, min(2.0, controls.speed))
    base = max(0.6, len(words) / (2.5 * speed))
    pause = max(0, controls.pause_ms) / 1000.0
    return round(base + pause, 3)


def score_quality(
    *,
    text: str,
    language: str,
    controls: VoiceControls,
    has_ssml: bool,
) -> VoiceQuality:
    naturalness = 0.78
    clarity = 0.8
    prosody = 0.75

    if len(text.strip()) >= 12:
        naturalness += 0.08
    if language in ("en", "ur", "hi", "ar", "pa"):
        clarity += 0.05
    if 0.85 <= controls.speed <= 1.15:
        prosody += 0.08
    if abs(controls.pitch) <= 4:
        prosody += 0.05
    if has_ssml:
        naturalness += 0.04
    if controls.pronunciation_hints:
        clarity += 0.04

    naturalness = min(0.98, naturalness)
    clarity = min(0.98, clarity)
    prosody = min(0.98, prosody)
    overall = round((naturalness * 0.4 + clarity * 0.35 + prosody * 0.25), 3)

    if overall >= 0.9:
        grade = "A"
    elif overall >= 0.8:
        grade = "B"
    elif overall >= 0.7:
        grade = "C"
    else:
        grade = "D"

    return VoiceQuality(
        overall=overall,
        naturalness=round(naturalness, 3),
        clarity=round(clarity, 3),
        prosody=round(prosody, 3),
        grade=grade,
    )
