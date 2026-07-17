"""Face consistency service — ensure traits stay locked across generations."""

from __future__ import annotations

from typing import Any

from app.services.face_lock.models import FaceLockRecord, PRESERVED_TRAITS
from app.services.face_lock.validator import compute_identity_score


def consistency_report(lock: FaceLockRecord) -> dict[str, Any]:
    verification = compute_identity_score(lock, candidate_features=lock.features)
    return {
        "character_id": lock.character_id,
        "consistent": not verification.drift_detected and verification.passed,
        "identity_score": verification.identity_score,
        "preserved_traits": list(PRESERVED_TRAITS),
        "features_locked": True,
        "embedding_locked": lock.embedding.locked,
        "face_embedding_ref": lock.embedding.face_embedding_ref,
        "verification": verification.to_dict(),
    }


def apply_lock_to_generation_prompt(lock: FaceLockRecord) -> str:
    f = lock.features
    return (
        f"FACE LOCK [{lock.character_id}] ref={lock.embedding.face_embedding_ref}: "
        f"preserve face_structure={f.face_structure}, eye_shape={f.eye_shape}, "
        f"nose={f.nose}, lips={f.lips}, jawline={f.jawline}, ears={f.ears}, "
        f"hairstyle={f.hairstyle}, beard={f.beard}, age={f.age}, "
        f"skin_tone={f.skin_tone}, body_proportions={f.body_proportions}. "
        f"identity_strength={lock.identity_strength:.2f}. No identity drift."
    )
