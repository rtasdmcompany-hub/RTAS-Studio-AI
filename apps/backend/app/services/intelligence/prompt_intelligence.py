"""Module 1 — Prompt Intelligence Engine (structured analysis only)."""

from __future__ import annotations

import re
from typing import Any

from app.services.intelligence.models import PromptIntelligenceResult

_URDU_RE = re.compile(r"[\u0600-\u06FF]")
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")

_CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "song": ("song", "lyrics", "music video", "rap", "chorus", "beat"),
    "religious": ("religious", "islamic", "faith", "mosque", "prayer", "spiritual"),
    "business": ("business", "startup", "brand", "commercial", "corporate", "product"),
    "cartoon": ("cartoon", "animated", "kids", "comic", "anime"),
    "story": ("story", "narrative", "tale", "fiction", "drama"),
    "podcast": ("podcast", "talk", "interview", "host", "episode"),
}

_STYLE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "real": ("photoreal", "realistic", "cinematic real", "live action", "genuine"),
    "avatar": ("avatar", "digital human", "cgi face", "virtual influencer"),
    "cartoon": ("cartoon", "illustrated", "2d", "3d stylized", "toon"),
}

_EMOTION_KEYWORDS: dict[str, tuple[str, ...]] = {
    "inspiring": ("inspire", "hope", "uplift", "motivate"),
    "dramatic": ("dramatic", "intense", "tension", "epic"),
    "calm": ("calm", "peaceful", "soft", "serene"),
    "joyful": ("happy", "joy", "celebrate", "fun"),
    "somber": ("sad", "grief", "melancholy", "solemn"),
}

_GENRE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "commercial": ("ad", "commercial", "promo", "campaign"),
    "documentary": ("documentary", "interview", "real world"),
    "music_video": ("music video", "mv", "performance"),
    "narrative": ("story", "scene", "character arc"),
    "corporate": ("corporate", "pitch", "saas", "b2b"),
}

_CAMERA_HINTS: tuple[tuple[str, str], ...] = (
    ("drone", "aerial / drone"),
    ("tracking", "tracking shot"),
    ("close-up", "close-up"),
    ("close up", "close-up"),
    ("wide", "wide establishing"),
    ("handheld", "handheld"),
    ("steadicam", "steadicam"),
    ("slow motion", "slow motion"),
    ("macro", "macro detail"),
)

_LIGHTING_HINTS: tuple[tuple[str, str], ...] = (
    ("golden hour", "golden hour"),
    ("neon", "neon / night"),
    ("soft light", "soft diffused"),
    ("high contrast", "high contrast"),
    ("studio light", "studio keyed"),
    ("sunset", "sunset warm"),
    ("moonlight", "moonlit night"),
)


def _detect_language(text: str) -> str:
    if _URDU_RE.search(text):
        return "ur"
    if _CJK_RE.search(text):
        return "zh"
    return "en"


def _first_match(text: str, table: dict[str, tuple[str, ...]], default: str) -> str:
    for key, words in table.items():
        if any(w in text for w in words):
            return key
    return default


def analyze_prompt(
    prompt: str,
    *,
    category_hint: str | None = None,
    style_hint: str | None = None,
    duration_hint: int | None = None,
) -> PromptIntelligenceResult:
    raw = (prompt or "").strip()
    lower = raw.lower()

    language = _detect_language(raw)
    category = category_hint or _first_match(lower, _CATEGORY_KEYWORDS, "business")
    style = style_hint or _first_match(lower, _STYLE_KEYWORDS, "real")
    emotion = _first_match(lower, _EMOTION_KEYWORDS, "inspiring")
    genre = _first_match(lower, _GENRE_KEYWORDS, "commercial")

    camera_requirements = [label for key, label in _CAMERA_HINTS if key in lower]
    if not camera_requirements:
        camera_requirements = ["medium shot", "gentle push-in"]

    lighting = "natural balanced"
    for key, label in _LIGHTING_HINTS:
        if key in lower:
            lighting = label
            break

    estimated = duration_hint if duration_hint and duration_hint > 0 else 15
    if "long" in lower or "60" in lower:
        estimated = max(estimated, 60)
    elif "short" in lower or "15" in lower:
        estimated = min(estimated, 15)

    missing: list[str] = []
    if len(raw) < 12:
        missing.append("prompt_too_short")
    if style == "real" and "face" not in lower and "person" not in lower:
        missing.append("subject_identity_unclear")
    if "product" in lower and "brand" not in lower:
        missing.append("brand_name_optional")
    if not any(k in lower for k, _ in _LIGHTING_HINTS):
        missing.append("lighting_unspecified")

    confidence = 0.55
    if len(raw) >= 40:
        confidence += 0.2
    if category_hint:
        confidence += 0.1
    if style_hint:
        confidence += 0.1
    confidence = min(0.95, confidence)

    return PromptIntelligenceResult(
        language=language,
        category=category,
        style=style,
        emotion=emotion,
        camera_requirements=camera_requirements,
        lighting=lighting,
        cinematic_genre=genre,
        estimated_duration_seconds=int(estimated),
        missing_information=missing,
        confidence=round(confidence, 2),
    )


def analyze_prompt_dict(prompt: str, **kwargs: Any) -> dict[str, Any]:
    return analyze_prompt(prompt, **kwargs).to_dict()
