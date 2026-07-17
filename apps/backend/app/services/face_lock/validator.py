"""Identity validator — score 0–100 and drift detection."""

from __future__ import annotations

from typing import Any

from app.services.face_lock.embeddings import build_face_embedding, cosine_similarity
from app.services.face_lock.models import (
    DriftFlag,
    FaceFeatures,
    FaceLockRecord,
    IdentityVerification,
)
from app.services.face_lock.version import DRIFT_THRESHOLD


def _trait_mismatch(locked: FaceFeatures, candidate: FaceFeatures) -> list[DriftFlag]:
    flags: list[DriftFlag] = []
    pairs = [
        ("face_structure", locked.face_structure, candidate.face_structure, 0.9),
        ("eye_shape", locked.eye_shape, candidate.eye_shape, 0.85),
        ("nose", locked.nose, candidate.nose, 0.8),
        ("lips", locked.lips, candidate.lips, 0.75),
        ("jawline", locked.jawline, candidate.jawline, 0.8),
        ("ears", locked.ears, candidate.ears, 0.6),
        ("hairstyle", locked.hairstyle, candidate.hairstyle, 0.7),
        ("beard", locked.beard, candidate.beard, 0.65),
        ("skin_tone", locked.skin_tone, candidate.skin_tone, 0.85),
        ("body_proportions", locked.body_proportions, candidate.body_proportions, 0.7),
    ]
    for trait, a, b, sev in pairs:
        if str(a).lower() != str(b).lower():
            flags.append(
                DriftFlag(
                    trait=trait,
                    severity=sev,
                    detail=f"{trait} changed: '{a}' → '{b}'",
                )
            )
    age_delta = abs(int(locked.age) - int(candidate.age))
    if age_delta > 2:
        flags.append(
            DriftFlag(
                trait="age",
                severity=min(1.0, age_delta / 20.0),
                detail=f"age drift: {locked.age} → {candidate.age}",
            )
        )
    return flags


def compute_identity_score(
    lock: FaceLockRecord,
    *,
    candidate_features: FaceFeatures | None = None,
    candidate_reference_url: str | None = None,
) -> IdentityVerification:
    candidate = candidate_features or lock.features
    flags = _trait_mismatch(lock.features, candidate)

    # Embedding similarity vs locked embedding (candidate from same DNA → ~1.0)
    cand_emb = build_face_embedding(
        character_id=lock.character_id,
        features_fingerprint=candidate.fingerprint(),
        reference_url=candidate_reference_url
        or (lock.reference.url if lock.reference else None),
        regenerate=True,  # build candidate vector for comparison only
        existing=None,
    )
    sim = cosine_similarity(lock.embedding.vector, cand_emb.vector)
    # Map cosine [-1,1] → [0,100], same-seed near 100
    emb_score = max(0.0, min(100.0, (sim + 1.0) * 50.0))
    if candidate.fingerprint() == lock.features.fingerprint() and not flags:
        emb_score = max(emb_score, 98.0)

    trait_penalty = sum(f.severity * 12.0 for f in flags)
    score = max(0.0, min(100.0, emb_score - trait_penalty))
    # Perfect match boost
    if not flags and sim >= 0.99:
        score = max(score, 99.0)

    drift = score < DRIFT_THRESHOLD or len(flags) > 0 and score < 90
    # Same identity: no drift
    if not flags and score >= DRIFT_THRESHOLD:
        drift = False

    notes: list[str] = []
    if drift:
        notes.append("identity_drift_flagged")
    else:
        notes.append("identity_stable")
    notes.append(f"face_embedding_ref={lock.embedding.face_embedding_ref}")

    return IdentityVerification(
        character_id=lock.character_id,
        identity_score=round(score, 2),
        passed=score >= DRIFT_THRESHOLD,
        drift_detected=drift,
        drift_flags=flags,
        cosine_similarity=round(sim, 4),
        notes=notes,
    )


def validate_lock_request(
    *,
    character_id: str | None,
    reference_url: str | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    cid = (character_id or "").strip()
    if not cid:
        errors.append("character_id is required")
    if reference_url is not None and len(reference_url) > 4000:
        errors.append("reference_url too long")
    return {"ok": len(errors) == 0, "errors": errors, "character_id": cid}
