"""Language-aware phoneme detection from dialogue text."""

from __future__ import annotations

import re

from app.services.lip_sync.models import PhonemeToken, SupportedLanguage

_LATIN_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^(sh|ch|th|ph|wh)", re.I), "SH"),
    (re.compile(r"^[aeiou]+", re.I), "AA"),
    (re.compile(r"^[bpm]", re.I), "P"),
    (re.compile(r"^[fv]", re.I), "F"),
    (re.compile(r"^[szc]", re.I), "S"),
    (re.compile(r"^[tdn]", re.I), "T"),
    (re.compile(r"^[kgq]", re.I), "K"),
    (re.compile(r"^[lr]", re.I), "L"),
    (re.compile(r"^[w]", re.I), "W"),
    (re.compile(r"^[yj]", re.I), "Y"),
    (re.compile(r"^[m]", re.I), "M"),
]

# Unicode escapes keep source encoding-safe on Windows.
_ARABIC_CLASS: list[tuple[str, str]] = [
    ("\u0627\u0623\u0625\u0622\u0639\u063a", "AA"),
    ("\u0628\u067e", "P"),
    ("\u062a\u0641\u0637", "T"),
    ("\u062b\u0633\u0635\u0632\u0638", "S"),
    ("\u062c\u062d\u062e\u0647", "H"),
    ("\u062f\u0630\u0636", "D"),
    ("\u0631", "R"),
    ("\u0634\u0642", "SH"),
    ("\u0643\u06af", "K"),
    ("\u0644", "L"),
    ("\u0645", "M"),
    ("\u0646", "N"),
    ("\u0648\u0624", "W"),
    ("\u064a\u0626\u0649", "Y"),
    ("\u0641", "F"),
]

_DEVANAGARI_CLASS: list[tuple[str, str]] = [
    ("\u0905\u0906\u0907\u0908\u0909\u090a\u090f\u0910\u0913\u0914", "AA"),
    ("\u0915\u0916\u0917\u0918\u0919", "K"),
    ("\u091a\u091b\u091c\u091d\u091e", "CH"),
    ("\u091f\u0920\u0921\u0922\u0923\u0924\u0925\u0926\u0927\u0928", "T"),
    ("\u092a\u092b\u092c\u092d\u092e", "P"),
    ("\u092f\u0930\u0932\u0935", "L"),
    ("\u0936\u0937\u0938\u0939", "SH"),
]

_GURMUKHI_CLASS: list[tuple[str, str]] = [
    ("\u0a05\u0a06\u0a07\u0a08\u0a09\u0a0a\u0a0f\u0a10\u0a13\u0a14", "AA"),
    ("\u0a15\u0a16\u0a17\u0a18\u0a19", "K"),
    ("\u0a1a\u0a1b\u0a1c\u0a1d\u0a1e", "CH"),
    ("\u0a1f\u0a20\u0a21\u0a22\u0a23\u0a24\u0a25\u0a26\u0a27\u0a28", "T"),
    ("\u0a2a\u0a2b\u0a2c\u0a2d\u0a2e", "P"),
    ("\u0a2f\u0a30\u0a32\u0a35", "L"),
    ("\u0a38\u0a39\u0a36", "SH"),
]


def _tokenize(text: str, language: SupportedLanguage) -> list[str]:
    if language in ("ur", "ar"):
        return re.findall(r"[\u0600-\u06FF]+|[A-Za-z']+", text or "")
    if language == "hi":
        return re.findall(r"[\u0900-\u097F]+|[A-Za-z']+", text or "")
    if language == "pa":
        return re.findall(r"[\u0A00-\u0A7F]+|[\u0600-\u06FF]+|[A-Za-z']+", text or "")
    return re.findall(r"[A-Za-z']+", text or "")


def _latin_phoneme(token: str) -> str:
    for pattern, ph in _LATIN_RULES:
        if pattern.search(token):
            return ph
    return "REST"


def _script_phoneme(token: str, classes: list[tuple[str, str]]) -> str:
    for ch in token:
        for letters, ph in classes:
            if ch in letters:
                return ph
    return "AA"


def grapheme_to_phoneme(token: str, language: SupportedLanguage) -> str:
    if not token:
        return "SIL"
    if re.match(r"^[A-Za-z']+$", token):
        return _latin_phoneme(token)
    if re.search(r"[\u0900-\u097F]", token):
        return _script_phoneme(token, _DEVANAGARI_CLASS)
    if re.search(r"[\u0A00-\u0A7F]", token):
        return _script_phoneme(token, _GURMUKHI_CLASS)
    if re.search(r"[\u0600-\u06FF]", token):
        return _script_phoneme(token, _ARABIC_CLASS)
    return _latin_phoneme(token)


def detect_phonemes(
    dialogue: str,
    language: SupportedLanguage,
    *,
    start_sec: float,
    end_sec: float,
) -> list[PhonemeToken]:
    tokens = _tokenize(dialogue, language)
    if not tokens:
        return [
            PhonemeToken(
                index=0,
                grapheme="",
                phoneme="SIL",
                language=language,
                start_sec=start_sec,
                end_sec=end_sec,
                stress=0.0,
            )
        ]

    span = max(0.05, end_sec - start_sec)
    slot = span / len(tokens)
    out: list[PhonemeToken] = []
    t = start_sec
    for i, tok in enumerate(tokens):
        ph = grapheme_to_phoneme(tok, language)
        stress = 0.75 if ph in ("AA", "W", "Y") else 0.45
        out.append(
            PhonemeToken(
                index=i,
                grapheme=tok,
                phoneme=ph,
                language=language,
                start_sec=round(t, 3),
                end_sec=round(t + slot, 3),
                stress=stress,
            )
        )
        t += slot
    return out
