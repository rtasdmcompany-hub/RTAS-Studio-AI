"""Module 1 — Prompt Intelligence Engine (structured analysis only)."""

from __future__ import annotations

import re
from typing import Any

from app.services.intelligence.models import PromptIntelligenceResult
from app.services.intelligence.prompt_understanding import (
    to_prompt_intelligence,
    understand_prompt,
)
from app.services.intelligence.prompt_understanding.models import (
    CinematicPromptUnderstanding,
)

_URDU_RE = re.compile(r"[\u0600-\u06FF]")
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def _detect_language(text: str) -> str:
    if _URDU_RE.search(text):
        return "ur"
    if _CJK_RE.search(text):
        return "zh"
    return "en"


def analyze_prompt(
    prompt: str,
    *,
    category_hint: str | None = None,
    style_hint: str | None = None,
    duration_hint: int | None = None,
    understanding: CinematicPromptUnderstanding | None = None,
) -> PromptIntelligenceResult:
    """
    Analyze a prompt for the legacy intelligence contract.

    Internally driven by the Cinematic Prompt Understanding Engine so
    Character Memory / Director / Continuity remain compatible.
    """
    raw = (prompt or "").strip()
    language = _detect_language(raw)
    parsed = understanding or understand_prompt(raw, category_hint=category_hint)
    return to_prompt_intelligence(
        parsed,
        language=language,
        style_hint=style_hint,
        duration_hint=duration_hint,
    )


def analyze_prompt_dict(prompt: str, **kwargs: Any) -> dict[str, Any]:
    return analyze_prompt(prompt, **kwargs).to_dict()
