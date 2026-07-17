"""Pluggable localization language registry — unlimited future languages."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class LanguageProfile:
    code: str
    name: str
    native_name: str
    rtl: bool = False
    default_locale: str = "en-US"
    accent_default: str = "neutral"
    script: str = "latin"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_REGISTRY: dict[str, LanguageProfile] = {}


def _register_defaults() -> None:
    defaults = [
        LanguageProfile("en", "English", "English", default_locale="en-US"),
        LanguageProfile("ur", "Urdu", "اردو", rtl=True, default_locale="ur-PK", script="arabic"),
        LanguageProfile("hi", "Hindi", "हिन्दी", default_locale="hi-IN", script="devanagari"),
        LanguageProfile("ar", "Arabic", "العربية", rtl=True, default_locale="ar-SA", script="arabic"),
        LanguageProfile("pa", "Punjabi", "ਪੰਜਾਬੀ", default_locale="pa-IN", script="gurmukhi"),
        LanguageProfile("tr", "Turkish", "Türkçe", default_locale="tr-TR"),
        LanguageProfile("es", "Spanish", "Español", default_locale="es-ES"),
        LanguageProfile("fr", "French", "Français", default_locale="fr-FR"),
        LanguageProfile("de", "German", "Deutsch", default_locale="de-DE"),
        LanguageProfile("zh", "Chinese", "中文", default_locale="zh-CN", script="han"),
        LanguageProfile("ja", "Japanese", "日本語", default_locale="ja-JP", script="japanese"),
        LanguageProfile("ko", "Korean", "한국어", default_locale="ko-KR", script="hangul"),
    ]
    for p in defaults:
        _REGISTRY[p.code] = p


_register_defaults()


def register_language(profile: LanguageProfile) -> None:
    _REGISTRY[profile.code.lower().strip()] = profile


def normalize_language(code: str | None) -> str:
    if not code:
        return "en"
    key = code.strip().lower().replace("_", "-")
    aliases = {
        "zh-cn": "zh",
        "zh-tw": "zh",
        "cmn": "zh",
        "jp": "ja",
        "kor": "ko",
        "spa": "es",
        "fra": "fr",
        "deu": "de",
        "tur": "tr",
    }
    if key in aliases:
        key = aliases[key]
    if key in _REGISTRY:
        return key
    short = key.split("-")[0]
    if short in _REGISTRY:
        return short
    raise ValueError(
        f"Unsupported language '{code}'. Register via register_language()."
    )


def get_language(code: str | None) -> LanguageProfile:
    return _REGISTRY[normalize_language(code)]


def is_supported(code: str | None) -> bool:
    try:
        normalize_language(code)
        return True
    except ValueError:
        return False


def list_languages() -> list[dict[str, Any]]:
    return [p.to_dict() for p in sorted(_REGISTRY.values(), key=lambda x: x.name)]
