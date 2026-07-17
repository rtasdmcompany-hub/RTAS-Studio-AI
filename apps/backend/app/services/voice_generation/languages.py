"""Pluggable language registry — add languages without changing core engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LanguageSpec:
    code: str
    name: str
    native_name: str
    rtl: bool = False
    default_locale: str = "en-US"

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "native_name": self.native_name,
            "rtl": self.rtl,
            "default_locale": self.default_locale,
        }


_REGISTRY: dict[str, LanguageSpec] = {
    "en": LanguageSpec("en", "English", "English", default_locale="en-US"),
    "ur": LanguageSpec("ur", "Urdu", "اردو", rtl=True, default_locale="ur-PK"),
    "hi": LanguageSpec("hi", "Hindi", "हिन्दी", default_locale="hi-IN"),
    "ar": LanguageSpec("ar", "Arabic", "العربية", rtl=True, default_locale="ar-SA"),
    "pa": LanguageSpec("pa", "Punjabi", "ਪੰਜਾਬੀ", default_locale="pa-IN"),
}


def register_language(spec: LanguageSpec) -> None:
    """Extend supported languages without modifying core generation logic."""
    _REGISTRY[spec.code.lower()] = spec


def list_languages() -> list[dict[str, Any]]:
    return [s.to_dict() for s in sorted(_REGISTRY.values(), key=lambda s: s.code)]


def normalize_language(code: str | None) -> str:
    if not code:
        return "en"
    key = code.strip().lower().replace("_", "-")
    if key in _REGISTRY:
        return key
    short = key.split("-")[0]
    if short in _REGISTRY:
        return short
    raise ValueError(
        f"Unsupported language '{code}'. Supported: {', '.join(sorted(_REGISTRY))}"
    )


def is_supported_language(code: str | None) -> bool:
    try:
        normalize_language(code)
        return True
    except ValueError:
        return False


def get_language(code: str | None) -> LanguageSpec:
    return _REGISTRY[normalize_language(code)]
