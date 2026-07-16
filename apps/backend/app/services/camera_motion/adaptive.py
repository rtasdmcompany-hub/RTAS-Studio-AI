"""
Adaptive Camera Logic.

Chooses professional camera motion from scene context, subject locomotion,
director pacing, emotion, and explicit camera plans.
"""

from __future__ import annotations

from typing import Any

from app.services.camera_motion.detector import detect_primary_candidates
from app.services.camera_motion.models import AdaptiveDecision, CameraMotionKind

# Subject locomotion → preferred camera follow language
_LOCO_BIAS: dict[str, list[CameraMotionKind]] = {
    "walking": ["tracking", "steadicam", "dolly"],
    "running": ["tracking", "handheld", "steadicam"],
    "sitting": ["push_in", "slider", "static"],
    "standing": ["orbit", "push_in", "slider"],
    "turning": ["orbit", "slider", "steadicam"],
    "looking": ["push_in", "static", "slider"],
    "idle": ["static", "slider", "push_in"],
}

_EMOTION_BIAS: dict[str, list[CameraMotionKind]] = {
    "tense": ["handheld", "push_in", "tracking"],
    "intense": ["handheld", "push_in", "tracking"],
    "angry": ["handheld", "push_in"],
    "sad": ["push_in", "dolly", "static"],
    "lonely": ["pull_out", "drone", "crane"],
    "romance": ["orbit", "push_in", "slider"],
    "romantic": ["orbit", "push_in", "slider"],
    "confident": ["steadicam", "tracking", "dolly"],
    "epic": ["crane", "drone", "orbit"],
    "calm": ["slider", "dolly", "static"],
    "joyful": ["orbit", "steadicam", "tracking"],
    "happy": ["orbit", "steadicam"],
}


def _director_pacing_bias(pacing: str | None) -> list[CameraMotionKind]:
    p = (pacing or "").lower()
    if any(x in p for x in ("fast", "urgent", "intense", "rising")):
        return ["tracking", "handheld", "push_in"]
    if any(x in p for x in ("slow", "gentle", "intimate", "calm")):
        return ["dolly", "push_in", "slider"]
    if "reveal" in p:
        return ["pull_out", "crane", "drone"]
    return []


def choose_camera_motion(
    text: str,
    *,
    camera: dict[str, Any] | None = None,
    actions: list[str] | None = None,
    locomotion: str | None = None,
    emotion: str | None = None,
    director_pacing: str | None = None,
    cinematic_rhythm: str | None = None,
) -> AdaptiveDecision:
    candidates = detect_primary_candidates(text, camera=camera, actions=actions)
    scores: dict[CameraMotionKind, float] = {k: s for k, s in candidates}

    def bump(kind: CameraMotionKind, amount: float) -> None:
        scores[kind] = scores.get(kind, 0.0) + amount

    loco = (locomotion or "").lower().strip()
    for i, kind in enumerate(_LOCO_BIAS.get(loco, [])):
        bump(kind, 0.35 - i * 0.08)

    emo = (emotion or "").lower().strip()
    for key, kinds in _EMOTION_BIAS.items():
        if key in emo:
            for i, kind in enumerate(kinds):
                bump(kind, 0.3 - i * 0.07)
            break

    for i, kind in enumerate(_director_pacing_bias(director_pacing)):
        bump(kind, 0.25 - i * 0.06)

    rhythm = (cinematic_rhythm or "").lower()
    if any(x in rhythm for x in ("rising", "build", "crescendo")):
        bump("push_in", 0.2)
        bump("tracking", 0.15)
    if any(x in rhythm for x in ("epic", "grand", "sweeping")):
        bump("crane", 0.25)
        bump("drone", 0.2)
        bump("orbit", 0.15)

    # Explicit camera plan wins hard if present
    if camera:
        from app.services.camera_motion.detector import detect_from_camera_plan

        planned = detect_from_camera_plan(camera)
        if planned:
            bump(planned, 0.85)

    if not scores:
        # Sensible default by locomotion
        default: CameraMotionKind = "steadicam" if loco in ("walking", "running") else "push_in"
        return AdaptiveDecision(
            chosen=default,
            reason="fallback default — no strong motion cues",
            alternatives=["dolly", "slider", "static"],
            factors={
                "locomotion": loco or None,
                "emotion": emo or None,
                "pacing": director_pacing,
            },
        )

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    chosen = ranked[0][0]
    alts = [k for k, _ in ranked[1:4]]
    reasons = [f"score:{chosen}={ranked[0][1]:.2f}"]
    if loco:
        reasons.append(f"locomotion={loco}")
    if emo:
        reasons.append(f"emotion={emo}")
    if director_pacing:
        reasons.append(f"pacing={director_pacing}")
    if camera and (camera.get("movement") or camera.get("cinematic_motion")):
        reasons.append(
            f"camera_plan={camera.get('cinematic_motion') or camera.get('movement')}"
        )

    return AdaptiveDecision(
        chosen=chosen,
        reason="; ".join(reasons),
        alternatives=alts,
        factors={
            "scores": {k: round(v, 3) for k, v in ranked[:6]},
            "locomotion": loco or None,
            "emotion": emo or None,
            "pacing": director_pacing,
            "rhythm": cinematic_rhythm,
        },
    )
