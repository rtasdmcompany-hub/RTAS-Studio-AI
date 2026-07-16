"""Detect subject cast type: single, two, family, crowd, animals, vehicles."""

from __future__ import annotations

import re

from app.services.intelligence.character_consistency.models import SubjectKind


def detect_subject_kind(prompt: str, character_count: int = 1) -> SubjectKind:
    text = (prompt or "").lower()

    if re.search(
        r"\b(car|truck|bike|motorcycle|vehicle|bus|van|jeep|suv)\b", text
    ):
        # Vehicle can co-exist with people; prefer vehicle when it's the hero subject.
        if re.search(r"\b(driving|parked|speeding|vehicle hero|product car)\b", text):
            return "vehicle"

    if re.search(
        r"\b(dog|cat|horse|bird|animal|lion|tiger|elephant|pet)\b", text
    ):
        if not re.search(r"\b(man|woman|person|people|family)\b", text):
            return "animal"
        # People + animal → still character-led unless animal is sole focus
        if re.search(r"\b(with (his|her|their) (dog|cat|horse|pet))\b", text):
            pass
        elif re.search(r"\b(a (dog|cat|horse|lion) )\b", text) and character_count <= 1:
            return "animal"

    if re.search(r"\b(crowd|audience|mob|protesters|fans| throng)\b", text) or re.search(
        r"\b(many people|dozens|hundreds)\b", text
    ):
        return "crowd"

    if re.search(r"\b(family|parents|mother|father|siblings|children|kids)\b", text):
        return "family"

    if character_count >= 2 or re.search(
        r"\b(two|both|pair|duo|couple)\b", text
    ):
        return "two_characters"

    return "single_character"


def expected_track_count(kind: SubjectKind, character_count: int) -> int:
    if kind == "crowd":
        return max(character_count, 3)
    if kind == "family":
        return max(character_count, 3)
    if kind == "two_characters":
        return max(character_count, 2)
    if kind in ("animal", "vehicle"):
        return max(1, min(character_count, 2))
    return max(1, character_count)
