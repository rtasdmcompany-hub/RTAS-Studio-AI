"""Detect preferred camera motion from prompt, scene, and camera plan text."""

from __future__ import annotations

import re
from typing import Any

from app.services.camera_motion.catalog import normalize_motion
from app.services.camera_motion.models import CameraMotionKind

_KEYWORD_WEIGHTS: list[tuple[CameraMotionKind, re.Pattern[str], float]] = [
    ("drone", re.compile(r"\b(drone|aerial|flyover|bird'?s.?eye|from above)\b", re.I), 1.0),
    ("crane", re.compile(r"\b(crane|jib|boom up|boom down|rising shot)\b", re.I), 0.95),
    ("orbit", re.compile(r"\b(orbit|circle around|arc around|360)\b", re.I), 0.9),
    ("tracking", re.compile(r"\b(tracking|track(?:ing)? shot|follow(?:ing)? (?:her|him|them|the))\b", re.I), 0.9),
    ("steadicam", re.compile(r"\b(steadicam|gimbal|walk.?and.?talk|floating cam)\b", re.I), 0.88),
    ("handheld", re.compile(r"\b(handheld|hand.?held|documentary shake|raw energy)\b", re.I), 0.85),
    ("slider", re.compile(r"\b(slider|lateral slide|parallax slide)\b", re.I), 0.82),
    ("dolly", re.compile(r"\b(dolly|on tracks|wheeled move)\b", re.I), 0.8),
    ("push_in", re.compile(r"\b(push.?in|dolly in|move closer|intensify)\b", re.I), 0.78),
    ("pull_out", re.compile(r"\b(pull.?out|pull back|reveal|widen out)\b", re.I), 0.78),
    ("pov", re.compile(r"\b(pov|point of view|first.?person|through (?:her|his|their) eyes)\b", re.I), 0.9),
]


def score_motions(text: str) -> dict[CameraMotionKind, float]:
    blob = (text or "").strip()
    scores: dict[CameraMotionKind, float] = {}
    if not blob:
        return scores
    for kind, pat, weight in _KEYWORD_WEIGHTS:
        if pat.search(blob):
            scores[kind] = max(scores.get(kind, 0.0), weight)
    # Also honor explicit catalog labels
    explicit = normalize_motion(blob)
    if explicit:
        scores[explicit] = max(scores.get(explicit, 0.0), 0.75)
    return scores


def detect_from_camera_plan(camera: dict[str, Any] | None) -> CameraMotionKind | None:
    if not camera:
        return None
    for key in ("cinematic_motion", "movement", "camera_movement", "motion"):
        kind = normalize_motion(str(camera.get(key) or ""))
        if kind:
            return kind
    return None


def detect_primary_candidates(
    text: str,
    *,
    camera: dict[str, Any] | None = None,
    actions: list[str] | None = None,
) -> list[tuple[CameraMotionKind, float]]:
    blob = " ".join(
        [
            text or "",
            " ".join(actions or []),
            str((camera or {}).get("movement") or ""),
            str((camera or {}).get("cinematic_motion") or ""),
        ]
    )
    scores = score_motions(blob)
    planned = detect_from_camera_plan(camera)
    if planned:
        scores[planned] = max(scores.get(planned, 0.0), 0.92)
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    return ranked
