"""Expression validator + emotion consistency (identity safe)."""

from __future__ import annotations

from typing import Any

from app.services.emotion_intelligence.models import (
    ConsistencyReport,
    FacialExpression,
    IDENTITY_SAFE_TRAITS,
)
from app.services.emotion_intelligence.version import (
    EXPRESSION_SCORE_THRESHOLD,
    IDENTITY_PRESERVE_THRESHOLD,
)


def validate_expression(expression: FacialExpression) -> dict[str, Any]:
    flags: list[str] = []
    score = float(expression.expression_score)
    if not expression.face_lock_respected:
        flags.append("face_lock_not_respected")
        score -= 40
    if expression.smile_intensity < 0 or expression.smile_intensity > 1:
        flags.append("smile_intensity_out_of_range")
        score -= 20
    if not expression.eye_movement or not expression.mouth_expression:
        flags.append("incomplete_expression")
        score -= 25
    score = max(0.0, min(100.0, score))
    return {
        "ok": score >= EXPRESSION_SCORE_THRESHOLD and not flags,
        "expression_score": round(score, 2),
        "flags": flags,
        "threshold": EXPRESSION_SCORE_THRESHOLD,
    }


def verify_consistency(
    *,
    character_id: str | None,
    expression: FacialExpression,
    face_embedding_ref: str | None,
    prior_emotion: str | None = None,
) -> ConsistencyReport:
    validation = validate_expression(expression)
    flags = list(validation["flags"])
    identity_preserved = bool(expression.face_lock_respected)
    if face_embedding_ref is None and character_id:
        # Soft note — still identity-safe if face lock flag holds
        pass
    if not identity_preserved:
        flags.append("identity_compromised")

    emotion_continuity = True
    if prior_emotion and prior_emotion != expression.emotion:
        # Allowed transitions; flag only extreme jumps without intensity buffer
        extreme = {("calm", "angry"), ("happy", "crying"), ("calm", "fear")}
        if (prior_emotion, expression.emotion) in extreme and expression.smile_intensity > 0.8:
            emotion_continuity = False
            flags.append("abrupt_emotion_jump")

    score = float(validation["expression_score"])
    if identity_preserved:
        score = max(score, IDENTITY_PRESERVE_THRESHOLD)
    consistent = (
        score >= EXPRESSION_SCORE_THRESHOLD
        and identity_preserved
        and emotion_continuity
    )
    notes = ["identity_safe_traits=" + ",".join(IDENTITY_SAFE_TRAITS)]
    notes.append("expression_stable" if consistent else "expression_issues")

    return ConsistencyReport(
        character_id=character_id,
        consistent=consistent,
        expression_score=round(score, 2),
        identity_preserved=identity_preserved,
        emotion_continuity=emotion_continuity,
        drift_flags=flags,
        notes=notes,
    )
