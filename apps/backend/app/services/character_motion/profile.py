"""Character motion profile + body consistency (no distortion)."""

from __future__ import annotations

from typing import Any

from app.services.character_motion.models import (
    BODY_PRESERVED_TRAITS,
    BodyConsistencyReport,
    CharacterMotionProfile,
)
from app.services.character_motion.version import BODY_CONSISTENCY_THRESHOLD


def _load_character_dict(character_id: str | None) -> dict[str, Any] | None:
    if not character_id:
        return None
    try:
        from app.services.character_generation.engine import get_character

        record = get_character(character_id)
        if record:
            return record.to_dict()
    except Exception:
        pass
    return None


def _load_face_identity_ref(character_id: str | None) -> str | None:
    if not character_id:
        return None
    try:
        from app.services.face_lock import get_identity

        identity = get_identity(character_id)
        if identity:
            return identity.get("face_embedding_ref")
    except Exception:
        pass
    return None


def _load_appearance(character_id: str | None) -> dict[str, Any] | None:
    if not character_id:
        return None
    try:
        from app.services.appearance import get_style

        return get_style(character_id)
    except Exception:
        return None


def build_motion_profile(
    character_id: str | None,
    *,
    overrides: dict[str, Any] | None = None,
) -> CharacterMotionProfile:
    cid = (character_id or "anonymous").strip() or "anonymous"
    char = _load_character_dict(cid) or {}
    identity = char.get("identity") if isinstance(char.get("identity"), dict) else {}
    appearance = _load_appearance(cid) or {}
    profile_data = appearance.get("profile") if isinstance(appearance.get("profile"), dict) else {}
    dna = char.get("dna") if isinstance(char.get("dna"), dict) else {}

    base = {
        "character_id": cid,
        "face_identity_ref": _load_face_identity_ref(cid),
        "body_shape": str(
            profile_data.get("body_type")
            or identity.get("body_type")
            or "average"
        ),
        "height": str(profile_data.get("height") or "average"),
        "weight": str((overrides or {}).get("weight") or "average"),
        "body_proportions": str(
            identity.get("body_type") or profile_data.get("body_type") or "balanced"
        ),
        "walking_style": "natural",
        "running_style": "athletic",
        "gesture_style": "natural",
        "eye_contact": "natural",
        "head_movement": "subtle",
        "dna_fingerprint": dna.get("fingerprint"),
    }
    if overrides:
        base.update({k: v for k, v in overrides.items() if v is not None and k in base})
    return CharacterMotionProfile(**base)  # type: ignore[arg-type]


def validate_body_consistency(
    locked: CharacterMotionProfile,
    candidate: CharacterMotionProfile | None = None,
) -> BodyConsistencyReport:
    cand = candidate or locked
    flags: list[str] = []
    checks = [
        ("face_identity", locked.face_identity_ref, cand.face_identity_ref),
        ("body_shape", locked.body_shape, cand.body_shape),
        ("height", locked.height, cand.height),
        ("weight", locked.weight, cand.weight),
        ("body_proportions", locked.body_proportions, cand.body_proportions),
        ("walking_style", locked.walking_style, cand.walking_style),
        ("running_style", locked.running_style, cand.running_style),
        ("gesture_style", locked.gesture_style, cand.gesture_style),
        ("eye_contact", locked.eye_contact, cand.eye_contact),
        ("head_movement", locked.head_movement, cand.head_movement),
    ]
    for name, a, b in checks:
        if a != b:
            flags.append(f"{name}_drift:{a}->{b}")

    score = max(0.0, 100.0 - len(flags) * 12.0)
    if locked.fingerprint() == cand.fingerprint():
        score = max(score, 99.0)
    no_distortion = len(flags) == 0
    return BodyConsistencyReport(
        character_id=locked.character_id,
        consistent=score >= BODY_CONSISTENCY_THRESHOLD and no_distortion,
        score=round(score, 2),
        preserved_traits=list(BODY_PRESERVED_TRAITS),
        drift_flags=flags,
        no_body_distortion=no_distortion,
    )
