"""Appearance consistency + drift detection."""

from __future__ import annotations

from typing import Any

from app.services.appearance.models import (
    AppearanceDriftFlag,
    AppearanceProfile,
    AppearanceRecord,
    ConsistencyReport,
    FACIAL_IDENTITY_FIELDS,
)
from app.services.appearance.version import APPEARANCE_DRIFT_THRESHOLD


def _mismatch(
    trait: str,
    expected: Any,
    actual: Any,
    severity: float,
) -> AppearanceDriftFlag | None:
    a = expected if not isinstance(expected, list) else sorted(expected)
    b = actual if not isinstance(actual, list) else sorted(actual)
    if a != b:
        return AppearanceDriftFlag(
            trait=trait,
            severity=severity,
            detail=f"{trait} changed: {expected!r} → {actual!r}",
        )
    return None


def validate_appearance(
    record: AppearanceRecord,
    *,
    candidate: AppearanceProfile | None = None,
) -> ConsistencyReport:
    locked = record.profile
    cand = candidate or locked
    flags: list[AppearanceDriftFlag] = []

    face_fields = ("eye_color", "skin_tone")
    body_fields = ("body_type", "height")
    hair_fields = ("hairstyle", "hair_color", "beard_style")

    for trait, sev in (
        ("eye_color", 0.95),
        ("skin_tone", 0.9),
        ("body_type", 0.85),
        ("height", 0.7),
        ("hairstyle", 0.8),
        ("hair_color", 0.75),
        ("beard_style", 0.7),
        ("clothing_style", 0.55),
        ("shoes", 0.45),
    ):
        flag = _mismatch(trait, getattr(locked, trait), getattr(cand, trait), sev)
        if flag:
            flags.append(flag)

    acc_flag = _mismatch(
        "accessories",
        list(locked.accessories),
        list(cand.accessories),
        0.4,
    )
    if acc_flag:
        flags.append(acc_flag)

    # Facial identity must never drift (outfit switches must keep these equal)
    facial_ok = locked.facial_fingerprint() == cand.facial_fingerprint()
    face_preserved = all(
        getattr(locked, f) == getattr(cand, f) for f in face_fields
    )
    body_preserved = all(
        getattr(locked, f) == getattr(cand, f) for f in body_fields
    )
    hair_preserved = all(
        getattr(locked, f) == getattr(cand, f) for f in hair_fields
    )
    clothing_match = locked.clothing_style == cand.clothing_style
    accessories_match = sorted(locked.accessories) == sorted(cand.accessories)

    penalty = sum(f.severity * 14.0 for f in flags)
    score = max(0.0, min(100.0, 100.0 - penalty))
    if not flags:
        score = max(score, 99.0)

    # Any trait mismatch (including clothing/accessories) is appearance drift.
    # Facial identity compromise is always critical.
    drift = len(flags) > 0 or score < APPEARANCE_DRIFT_THRESHOLD
    if not flags and score >= APPEARANCE_DRIFT_THRESHOLD:
        drift = False

    notes: list[str] = []
    if drift:
        notes.append("appearance_drift_flagged")
    else:
        notes.append("appearance_stable")
    if facial_ok:
        notes.append("facial_identity_preserved")
    else:
        notes.append("facial_identity_compromised")

    return ConsistencyReport(
        character_id=record.character_id,
        consistent=not drift and score >= APPEARANCE_DRIFT_THRESHOLD,
        appearance_score=round(score, 2),
        drift_detected=drift,
        drift_flags=flags,
        face_preserved=face_preserved,
        body_preserved=body_preserved,
        hair_preserved=hair_preserved,
        clothing_match=clothing_match,
        accessories_match=accessories_match,
        notes=notes,
    )


def validate_outfit_preserves_identity(
    before: AppearanceProfile,
    after: AppearanceProfile,
) -> dict[str, Any]:
    """Outfit switch must keep facial fingerprint identical."""
    ok = before.facial_fingerprint() == after.facial_fingerprint()
    changed_facial = [
        f
        for f in FACIAL_IDENTITY_FIELDS
        if getattr(before, f) != getattr(after, f)
    ]
    return {
        "ok": ok and not changed_facial,
        "facial_fingerprint_before": before.facial_fingerprint(),
        "facial_fingerprint_after": after.facial_fingerprint(),
        "changed_facial_fields": changed_facial,
        "clothing_changed": before.clothing_style != after.clothing_style,
    }
