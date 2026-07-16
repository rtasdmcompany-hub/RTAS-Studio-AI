"""Identity verification + drift detection across scenes/shots."""

from __future__ import annotations

from typing import Any

from app.services.intelligence.character_consistency.embeddings import (
    build_face_embedding,
    embedding_stability_score,
)
from app.services.intelligence.character_consistency.models import (
    ConsistencyScore,
    DriftFinding,
    IdentityProfile,
    VerificationResult,
)
from app.services.intelligence.models import ScenePlan, ShotPlan

_DRIFT_PATTERNS: tuple[tuple[str, str, float], ...] = (
    ("face swap", "face_swapping", 0.95),
    ("different face", "face_swapping", 0.9),
    ("new hairstyle", "hair_change", 0.85),
    ("hair cut", "hair_change", 0.8),
    ("change clothes", "clothing_drift", 0.85),
    ("different outfit", "clothing_drift", 0.8),
    ("wardrobe change", "clothing_drift", 0.75),
    ("looks older", "age_drift", 0.7),
    ("different person", "identity_drift", 0.95),
    ("another character", "identity_drift", 0.7),
)


def _strip_lock_language(text: str) -> str:
    """Remove identity-lock / forbid clauses so prevention text is not scored as drift."""
    lower = text.lower()
    for marker in ("identity lock", "forbidden:", "do not change face"):
        idx = lower.find(marker)
        if idx >= 0:
            text = text[:idx]
            lower = text.lower()
    return text


def _text_blob(scenes: list[ScenePlan], shots: list[ShotPlan]) -> str:
    parts: list[str] = []
    for s in scenes:
        parts.append(_strip_lock_language(s.description or ""))
        parts.append(s.title or "")
        parts.extend(s.actions or [])
    for sh in shots:
        parts.append(_strip_lock_language(sh.description or ""))
        parts.append(sh.action or "")
        parts.append(sh.title or "")
    return " ".join(parts).lower()


def verify_identity_consistency(
    *,
    profiles: list[IdentityProfile],
    scenes: list[ScenePlan],
    shots: list[ShotPlan],
    understanding: dict[str, Any] | None = None,
    pass_threshold: float = 0.72,
) -> VerificationResult:
    drifts: list[DriftFinding] = []
    notes: list[str] = []
    blob = _text_blob(scenes, shots)

    # Pattern-based drift scan
    for pattern, kind, severity in _DRIFT_PATTERNS:
        if pattern in blob:
            drifts.append(
                DriftFinding(
                    kind=kind,  # type: ignore[arg-type]
                    severity=severity,
                    subject_id=profiles[0].subject_id if profiles else "unknown",
                    scene_index=None,
                    shot_index=None,
                    detail=f"Detected drift cue in plan text: '{pattern}'",
                )
            )

    # Per-scene identity presence
    for scene in scenes:
        joined = f"{scene.description} {' '.join(scene.characters)}".lower()
        for profile in profiles:
            if profile.subject_id.lower() not in joined and "identity lock" not in joined:
                drifts.append(
                    DriftFinding(
                        kind="scene_mismatch",
                        severity=0.55,
                        subject_id=profile.subject_id,
                        scene_index=scene.index,
                        shot_index=None,
                        detail=f"Scene {scene.index} missing explicit identity lock for {profile.subject_id}",
                        auto_correctable=True,
                    )
                )

    # Emotion mismatch vs understanding
    mood = ""
    if understanding:
        emotions = understanding.get("emotion") or []
        if isinstance(emotions, list) and emotions:
            mood = str(emotions[0]).lower()
        else:
            mood = str(understanding.get("mood") or "").lower()
    if mood and profiles:
        for shot in shots:
            action = (shot.action or "").lower()
            if mood in ("sad", "lonely", "somber") and any(
                w in action for w in ("laugh", "celebrate", "party smile")
            ):
                drifts.append(
                    DriftFinding(
                        kind="emotion_mismatch",
                        severity=0.65,
                        subject_id=profiles[0].subject_id,
                        scene_index=shot.scene_index,
                        shot_index=shot.shot_index,
                        detail="Shot emotion conflicts with project mood",
                    )
                )

    # Embedding stability — re-derive from same traits/refs and compare
    emb_scores: list[float] = []
    for profile in profiles:
        traits_fp = (
            f"{profile.hair}|{profile.age}|{profile.skin_tone}|{profile.eye_color}|{profile.clothes}"
        )
        again, _ = build_face_embedding(
            subject_id=profile.subject_id,
            reference_image_urls=profile.reference_image_urls,
            traits_fingerprint=traits_fp,
        )
        # Use profile embedding vs regenerated; also simulate per-scene candidates
        candidates = [again for _ in scenes[:3]] or [again]
        emb_scores.append(
            embedding_stability_score(profile.face_embedding, candidates)
        )

    embedding_stability = (
        round(sum(emb_scores) / len(emb_scores), 4) if emb_scores else 0.5
    )

    # Score components
    face_pen = sum(d.severity for d in drifts if d.kind == "face_swapping")
    hair_pen = sum(d.severity for d in drifts if d.kind == "hair_change")
    cloth_pen = sum(d.severity for d in drifts if d.kind in ("clothing_drift", "accessory_drift"))
    id_pen = sum(d.severity for d in drifts if d.kind in ("identity_drift", "age_drift", "body_drift"))
    emo_pen = sum(d.severity for d in drifts if d.kind == "emotion_mismatch")
    scene_pen = sum(d.severity for d in drifts if d.kind == "scene_mismatch")

    def _clamp(v: float) -> float:
        return round(max(0.0, min(1.0, v)), 4)

    face = _clamp(1.0 - face_pen)
    hair = _clamp(1.0 - hair_pen)
    clothing = _clamp(1.0 - cloth_pen * 0.8)
    identity = _clamp(1.0 - id_pen * 0.9)
    expression = _clamp(1.0 - emo_pen * 0.8)
    scene_fit = _clamp(1.0 - scene_pen * 0.35)
    body = _clamp(1.0 - sum(d.severity for d in drifts if d.kind == "body_drift") * 0.9)

    # Bonus when locks present on scenes
    if scenes and all("identity lock" in (s.description or "").lower() for s in scenes):
        scene_fit = _clamp(scene_fit + 0.15)
        notes.append("All scenes include identity lock language")

    overall = _clamp(
        0.22 * identity
        + 0.18 * face
        + 0.12 * hair
        + 0.12 * clothing
        + 0.10 * body
        + 0.08 * expression
        + 0.10 * scene_fit
        + 0.08 * embedding_stability
    )

    score = ConsistencyScore(
        overall=overall,
        identity=identity,
        face=face,
        hair=hair,
        clothing=clothing,
        body=body,
        expression=expression,
        scene_fit=scene_fit,
        embedding_stability=embedding_stability,
        details={
            "drift_count": float(len(drifts)),
            "profile_count": float(len(profiles)),
        },
    )

    passed = overall >= pass_threshold and face_pen < 0.9 and id_pen < 0.9
    if not profiles:
        passed = False
        notes.append("No identity profiles to verify")

    return VerificationResult(
        passed=passed,
        score=score,
        drifts=drifts,
        verified_subject_ids=[p.subject_id for p in profiles],
        notes=notes,
    )
