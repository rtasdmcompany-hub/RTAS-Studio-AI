"""Face Lock & Identity Engine public operations."""

from __future__ import annotations

from typing import Any

from app.services.face_lock import store
from app.services.face_lock.consistency import apply_lock_to_generation_prompt, consistency_report
from app.services.face_lock.identity import features_from_overrides
from app.services.face_lock.lock_manager import lock_face
from app.services.face_lock.validator import compute_identity_score, validate_lock_request
from app.services.face_lock.version import ENGINE_LABEL, ENGINE_NAME, ENGINE_VERSION


def lock_character(
    character_id: str,
    **kwargs: Any,
) -> dict[str, Any]:
    record = lock_face(character_id, **kwargs)
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
        **record.to_dict(),
        "lock_prompt": apply_lock_to_generation_prompt(record),
    }


def verify_identity(
    character_id: str,
    *,
    feature_overrides: dict[str, Any] | None = None,
    candidate_reference_url: str | None = None,
) -> dict[str, Any]:
    validation = validate_lock_request(character_id=character_id)
    if not validation["ok"]:
        raise ValueError("; ".join(validation["errors"]))
    cid = validation["character_id"]
    lock = store.get_by_character(cid)
    if not lock:
        # Auto-lock baseline then verify
        lock = lock_face(cid)
    candidate = None
    if feature_overrides:
        candidate = features_from_overrides(lock.features, feature_overrides)
    verification = compute_identity_score(
        lock,
        candidate_features=candidate,
        candidate_reference_url=candidate_reference_url,
    )
    lock.last_verification = verification
    store.save(lock)
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        **verification.to_dict(),
        "face_embedding_ref": lock.embedding.face_embedding_ref,
        "lock_id": lock.lock_id,
        "consistency": consistency_report(lock),
    }


def get_identity(character_id: str) -> dict[str, Any] | None:
    lock = store.get_by_character(character_id)
    if not lock:
        return None
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
        **lock.to_dict(),
        "consistency": consistency_report(lock),
        "lock_prompt": apply_lock_to_generation_prompt(lock),
    }


def lock_dict(**kwargs: Any) -> dict[str, Any]:
    return lock_character(**kwargs)


def verify_dict(**kwargs: Any) -> dict[str, Any]:
    return verify_identity(**kwargs)
