"""Speaker verification + voice fingerprinting."""

from __future__ import annotations

import hashlib

from app.services.voice_cloning.models import VoiceFingerprint


def build_fingerprint(
    *,
    reference_url: str,
    checksum: str,
    sample_rate: int,
    duration_sec: float,
) -> VoiceFingerprint:
    seed = f"{reference_url}|{checksum}|{sample_rate}|{duration_sec}"
    digest = hashlib.sha1(seed.encode()).hexdigest()
    spectral = hashlib.md5(seed.encode()).hexdigest()[:16]
    # Simulated speaker score — deterministic, high for clean refs
    score = 0.72 + (int(digest[:2], 16) % 25) / 100.0
    return VoiceFingerprint(
        fingerprint_id=f"vfp_{digest[:12]}",
        checksum=checksum,
        embedding_ref=f"voice-embedding://{digest[:20]}",
        sample_rate=sample_rate,
        duration_sec=duration_sec,
        spectral_hash=spectral,
        speaker_score=round(min(0.99, score), 3),
    )


def verify_speaker(fingerprint: VoiceFingerprint, *, threshold: float = 0.7) -> bool:
    return fingerprint.speaker_score >= threshold


def similarity_score(a: VoiceFingerprint, b: VoiceFingerprint) -> float:
    if a.checksum == b.checksum:
        return 1.0
    # Partial overlap via spectral hash prefix
    shared = 0
    for x, y in zip(a.spectral_hash, b.spectral_hash):
        if x == y:
            shared += 1
    return round(shared / max(len(a.spectral_hash), 1), 3)
