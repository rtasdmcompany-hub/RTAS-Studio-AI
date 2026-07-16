"""Multi-language detection for Lip Sync Engine."""

from __future__ import annotations

import re
from typing import Any

from app.services.lip_sync.models import SupportedLanguage

_ARABIC_SCRIPT = re.compile(r"[\u0600-\u06FF]")
# Devanagari (Hindi)
_DEVANAGARI = re.compile(r"[\u0900-\u097F]")
# Gurmukhi (Punjabi)
_GURMUKHI = re.compile(r"[\u0A00-\u0A7F]")

_LANG_KEYWORDS: dict[SupportedLanguage, tuple[str, ...]] = {
    "ur": ("urdu", "pakistan", "pakistani", "اردو"),
    "ar": ("arabic", "quran", "nasheed", "عربي", "العربية"),
    "hi": ("hindi", "bollywood", "हिन्दी", "भारत"),
    "pa": ("punjabi", "panjabi", "ਪੰਜਾਬੀ", "پنجابی"),
    "en": ("english", "british", "american"),
}


def detect_language(
    text: str,
    *,
    hint: str | None = None,
    audio_director: dict[str, Any] | None = None,
) -> SupportedLanguage:
    if hint:
        h = hint.strip().lower()
        aliases = {
            "urdu": "ur",
            "english": "en",
            "arabic": "ar",
            "hindi": "hi",
            "punjabi": "pa",
            "panjabi": "pa",
        }
        mapped = aliases.get(h, h)
        if mapped in ("en", "ur", "ar", "hi", "pa"):
            return mapped  # type: ignore[return-value]

    det = (audio_director or {}).get("detection") or {}
    if isinstance(det, dict) and det.get("language"):
        lang = str(det["language"]).lower()
        if lang in ("en", "ur", "ar", "hi", "pa"):
            return lang  # type: ignore[return-value]
        if lang.startswith("ar"):
            return "ar"
        if lang.startswith("hi"):
            return "hi"

    raw = text or ""
    lower = raw.lower()

    if _GURMUKHI.search(raw) or any(k in lower for k in _LANG_KEYWORDS["pa"]):
        return "pa"
    if _DEVANAGARI.search(raw) or any(k in lower for k in _LANG_KEYWORDS["hi"]):
        return "hi"
    # Arabic script shared by Urdu/Arabic — disambiguate with keywords
    if _ARABIC_SCRIPT.search(raw):
        if any(k in lower for k in ("urdu", "pakistan", "pakistani", "اردو")):
            return "ur"
        if any(k in lower for k in ("arabic", "quran", "nasheed", "عربي")):
            return "ar"
        # Default Arabic-script South Asian dialogue → Urdu (RTAS market)
        return "ur"
    if any(k in lower for k in _LANG_KEYWORDS["ur"]):
        return "ur"
    if any(k in lower for k in _LANG_KEYWORDS["ar"]):
        return "ar"
    if any(k in lower for k in _LANG_KEYWORDS["hi"]):
        return "hi"
    if any(k in lower for k in _LANG_KEYWORDS["pa"]):
        return "pa"
    return "en"


def detect_all_languages(text: str) -> list[str]:
    """Return all languages that appear present (for mixed dialogue)."""
    found: list[str] = []
    raw = text or ""
    lower = raw.lower()
    if re.search(r"[A-Za-z]", raw) or "english" in lower:
        found.append("en")
    if _ARABIC_SCRIPT.search(raw) or any(k in lower for k in _LANG_KEYWORDS["ur"]):
        # may be ur or ar
        if any(k in lower for k in _LANG_KEYWORDS["ar"]) and "ur" not in found:
            found.append("ar")
        if "ur" not in found and (
            any(k in lower for k in _LANG_KEYWORDS["ur"]) or _ARABIC_SCRIPT.search(raw)
        ):
            found.append("ur")
    if _DEVANAGARI.search(raw) or any(k in lower for k in _LANG_KEYWORDS["hi"]):
        found.append("hi")
    if _GURMUKHI.search(raw) or any(k in lower for k in _LANG_KEYWORDS["pa"]):
        found.append("pa")
    primary = detect_language(text)
    if primary not in found:
        found.insert(0, primary)
    # unique preserve order
    out: list[str] = []
    for x in found:
        if x not in out:
            out.append(x)
    return out or ["en"]
