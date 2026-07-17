"""Translation engine + translation memory (simulation / deterministic)."""

from __future__ import annotations

import hashlib
import re
import threading
from typing import Any

from app.services.localization.languages import get_language, normalize_language

_lock = threading.Lock()
_MEMORY: dict[str, str] = {}
_MAX_MEM = 5000

# Lightweight phrase bank for natural-looking simulation
_PHRASES: dict[str, dict[str, str]] = {
    "ur": {
        "hello": "السلام علیکم",
        "welcome": "خوش آمدید",
        "thank you": "شکریہ",
        "goodbye": "خدا حافظ",
    },
    "hi": {
        "hello": "नमस्ते",
        "welcome": "स्वागत है",
        "thank you": "धन्यवाद",
        "goodbye": "अलविदा",
    },
    "ar": {
        "hello": "مرحبا",
        "welcome": "أهلا وسهلا",
        "thank you": "شكرا",
        "goodbye": "مع السلامة",
    },
    "pa": {
        "hello": "ਸਤ ਸ੍ਰੀ ਅਕਾਲ",
        "welcome": "ਜੀ ਆਇਆਂ ਨੂੰ",
        "thank you": "ਧੰਨਵਾਦ",
        "goodbye": "ਅਲਵਿਦਾ",
    },
    "tr": {"hello": "Merhaba", "welcome": "Hoş geldiniz", "thank you": "Teşekkürler"},
    "es": {"hello": "Hola", "welcome": "Bienvenido", "thank you": "Gracias"},
    "fr": {"hello": "Bonjour", "welcome": "Bienvenue", "thank you": "Merci"},
    "de": {"hello": "Hallo", "welcome": "Willkommen", "thank you": "Danke"},
    "zh": {"hello": "你好", "welcome": "欢迎", "thank you": "谢谢"},
    "ja": {"hello": "こんにちは", "welcome": "ようこそ", "thank you": "ありがとう"},
    "ko": {"hello": "안녕하세요", "welcome": "환영합니다", "thank you": "감사합니다"},
}


def _mem_key(source_lang: str, target_lang: str, text: str) -> str:
    digest = hashlib.sha1(
        f"{source_lang}|{target_lang}|{text.strip().lower()}".encode()
    ).hexdigest()
    return digest


def memory_get(source_lang: str, target_lang: str, text: str) -> str | None:
    with _lock:
        return _MEMORY.get(_mem_key(source_lang, target_lang, text))


def memory_put(source_lang: str, target_lang: str, text: str, translated: str) -> None:
    with _lock:
        _MEMORY[_mem_key(source_lang, target_lang, text)] = translated
        while len(_MEMORY) > _MAX_MEM:
            _MEMORY.pop(next(iter(_MEMORY)))


def memory_clear() -> None:
    with _lock:
        _MEMORY.clear()


def memory_size() -> int:
    with _lock:
        return len(_MEMORY)


def _apply_phrase_bank(text: str, target: str) -> str:
    bank = _PHRASES.get(target) or {}
    out = text
    for eng, loc in bank.items():
        out = re.sub(rf"\b{re.escape(eng)}\b", loc, out, flags=re.IGNORECASE)
    return out


def translate_text(
    text: str,
    *,
    source_language: str = "en",
    target_language: str = "en",
    context: str | None = None,
) -> dict[str, Any]:
    src = normalize_language(source_language)
    tgt = normalize_language(target_language)
    cleaned = (text or "").strip()
    if not cleaned:
        return {
            "translated_text": "",
            "from_memory": False,
            "source_language": src,
            "target_language": tgt,
        }

    cached = memory_get(src, tgt, cleaned)
    if cached is not None:
        return {
            "translated_text": cached,
            "from_memory": True,
            "source_language": src,
            "target_language": tgt,
        }

    if src == tgt:
        translated = cleaned
    else:
        lang = get_language(tgt)
        # Context-aware wrapper + phrase substitution (simulation)
        body = _apply_phrase_bank(cleaned, tgt)
        prefix = f"[{lang.code.upper()}]"
        if context:
            prefix = f"[{lang.code.upper()}|{context[:40]}]"
        if body == cleaned:
            # Deterministic transliteration-style marker when no phrase hit
            digest = hashlib.sha1(f"{tgt}|{cleaned}".encode()).hexdigest()[:6]
            translated = f"{prefix} {cleaned} ·{digest}"
        else:
            translated = f"{prefix} {body}"
        if lang.rtl and not any(ord(c) > 127 for c in translated):
            translated = f"{translated} ↩"

    memory_put(src, tgt, cleaned, translated)
    return {
        "translated_text": translated,
        "from_memory": False,
        "source_language": src,
        "target_language": tgt,
    }


def split_segments(text: str, *, duration_sec: float = 12.0) -> list[tuple[str, float, float]]:
    """Split text into timed segments for subtitles / dubbing."""
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", text.strip()) if p.strip()]
    if not parts:
        return [(text.strip() or "", 0.0, duration_sec)]
    each = duration_sec / len(parts)
    out: list[tuple[str, float, float]] = []
    t = 0.0
    for p in parts:
        out.append((p, round(t, 3), round(t + each, 3)))
        t += each
    return out
