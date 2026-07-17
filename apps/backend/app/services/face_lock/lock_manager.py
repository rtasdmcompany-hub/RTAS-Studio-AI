"""Face Lock Manager — create and update permanent identity locks."""

from __future__ import annotations

import hashlib
import time
from typing import Any

from app.services.face_lock import store
from app.services.face_lock.embeddings import build_face_embedding
from app.services.face_lock.identity import features_from_character, features_from_overrides
from app.services.face_lock.models import FaceLockRecord, PRESERVED_TRAITS
from app.services.face_lock.references import (
    build_reference,
    load_reference_payload,
    resolve_reference_kind,
)
from app.services.face_lock.validator import compute_identity_score, validate_lock_request
from app.services.face_lock.version import ENGINE_VERSION


def _lock_id(character_id: str) -> str:
    digest = hashlib.sha1(f"lock|{character_id}|{ENGINE_VERSION}".encode()).hexdigest()
    return f"flock_{digest[:12]}"


def _load_character_dict(character_id: str) -> dict[str, Any] | None:
    # Prefer engine module (works under package + importlib test loaders).
    try:
        from app.services.character_generation.engine import get_character

        record = get_character(character_id)
        if record:
            return record.to_dict()
    except Exception:
        pass
    try:
        from app.services.character_generation import get_character as get_char_pkg

        record = get_char_pkg(character_id)
        if record:
            return record.to_dict()
    except Exception:
        pass
    try:
        from app.services.character_generation import registry as reg

        for slot in ("Character_A", "Character_B", "Character_C"):
            if character_id == slot:
                rec = reg.get_slot(slot)  # type: ignore[arg-type]
                if rec:
                    return rec.to_dict()
            # Also resolve by character_id via registry helpers when available
            getter = getattr(reg, "get", None)
            if callable(getter):
                rec = getter(character_id)
                if rec:
                    return rec.to_dict()
                break
    except Exception:
        pass
    return None


def lock_face(
    character_id: str,
    *,
    reference_url: str | None = None,
    reference_kind: str | None = None,
    regenerate_embedding: bool = False,
    feature_overrides: dict[str, Any] | None = None,
    identity_strength: float = 0.95,
) -> FaceLockRecord:
    validation = validate_lock_request(
        character_id=character_id, reference_url=reference_url
    )
    if not validation["ok"]:
        raise ValueError("; ".join(validation["errors"]))

    cid = validation["character_id"]
    existing = store.get_by_character(cid)

    char_dict = _load_character_dict(cid) or {"character_id": cid}
    features = features_from_character(char_dict)
    features = features_from_overrides(features, feature_overrides)

    kind = resolve_reference_kind(reference_kind)
    # Prefer explicit URL; else stored/generated default
    ref = build_reference(
        cid,
        kind=kind if reference_url or kind != "uploaded" else "stored",
        url=reference_url,
        source=reference_kind or kind,
    )
    if kind == "uploaded" and not reference_url:
        raise ValueError("reference_url is required for uploaded reference")

    embedding = build_face_embedding(
        character_id=cid,
        features_fingerprint=features.fingerprint(),
        reference_url=ref.url if ref else None,
        regenerate=regenerate_embedding,
        existing=existing.embedding if existing else None,
    )

    version = (existing.version + 1) if existing and regenerate_embedding else (
        existing.version if existing else 1
    )
    record = FaceLockRecord(
        lock_id=existing.lock_id if existing else _lock_id(cid),
        character_id=cid,
        state="locked",
        features=features,
        embedding=embedding,
        reference=ref,
        preserved_traits=list(PRESERVED_TRAITS),
        identity_strength=max(0.5, min(1.0, float(identity_strength))),
        version=version,
        production_ready=True,
        metadata={
            "engine_version": ENGINE_VERSION,
            "reference_loaded": load_reference_payload(ref) if ref else None,
            "locked_at": time.time(),
            "embedding_regenerated": embedding.regenerated,
        },
    )
    # Baseline self-verification
    record.last_verification = compute_identity_score(record)
    store.save(record)
    return record
