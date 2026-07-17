"""Voice clone quality scoring."""

from __future__ import annotations

from app.services.voice_cloning.models import CloneQuality, VoiceFingerprint


def _grade(score: float) -> str:
    if score >= 0.9:
        return "A"
    if score >= 0.8:
        return "B"
    if score >= 0.7:
        return "C"
    return "D"


def score_clone_quality(
    *,
    fingerprint: VoiceFingerprint,
    reference_quality: float,
    speaker_verified: bool,
    locked: bool = False,
) -> CloneQuality:
    similarity = fingerprint.speaker_score
    clarity = min(0.99, 0.6 + reference_quality * 0.35)
    consistency = 0.88 if locked else 0.8
    if speaker_verified:
        consistency = min(0.99, consistency + 0.05)
    overall = round(
        similarity * 0.4 + clarity * 0.3 + consistency * 0.3,
        3,
    )
    return CloneQuality(
        overall=overall,
        similarity=round(similarity, 3),
        clarity=round(clarity, 3),
        consistency=round(consistency, 3),
        grade=_grade(overall),
        speaker_verified=speaker_verified,
    )
