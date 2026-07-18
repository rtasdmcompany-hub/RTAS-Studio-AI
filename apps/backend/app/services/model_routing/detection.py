"""Automatic request-type detection from prompt / hints."""

from __future__ import annotations

from app.services.model_routing.models import RequestType

_KEYWORDS: dict[RequestType, tuple[str, ...]] = {
    "code": ("python", "javascript", "typescript", " code", "function", "class ", "bug", "refactor", "compile"),
    "translation": ("translate", "translation", "into french", "into spanish", "into urdu", "into arabic", "localization"),
    "vision": ("describe this image", "what's in the photo", "analyze image", "vision", "screenshot", "ocr"),
    "image": (
        "generate an image",
        "generate image",
        "an image",
        "image of",
        "draw",
        "picture",
        "illustration",
        "png",
        "photo of",
        "artwork",
        "render an image",
    ),
    "video": (
        "generate video",
        "short video",
        " video",
        "animate",
        "cinematic video",
        "mp4",
        "film scene",
        "text to video",
        "video of",
        "make a video",
    ),
    "music": ("compose music", "soundtrack", "melody", "instrumental", "music for", "song instrumental"),
    "voice": ("text to speech", "tts", "voiceover", "narrate", "speak this", "clone voice", " warm voice", "voice"),
    "audio": ("generate audio", "sound effect", "sfx", "audio clip", "waveform"),
    "chat": ("chat", "conversation", "talk to me", "assistant", "roleplay"),
    "text": ("summarize", "write", "essay", "paragraph", "explain", "story"),
}


def detect_request_type(
    prompt: str,
    *,
    hint: str | None = None,
) -> tuple[RequestType, float, list[str]]:
    if hint:
        key = hint.strip().lower().replace(" ", "_")
        aliases = {
            "tts": "voice",
            "speech": "voice",
            "img": "image",
            "pic": "image",
            "vid": "video",
            "sfx": "audio",
            "coding": "code",
            "translate": "translation",
        }
        key = aliases.get(key, key)
        if key in _KEYWORDS:
            return key, 0.99, [f"hint={key}"]  # type: ignore[return-value]

    text = (prompt or "").lower()
    scores: dict[RequestType, float] = {k: 0.0 for k in _KEYWORDS}
    notes: list[str] = []
    for rtype, kws in _KEYWORDS.items():
        for kw in kws:
            if kw in text:
                scores[rtype] += 1.0
                notes.append(f"kw:{rtype}:{kw}")

    best = max(scores.items(), key=lambda kv: kv[1])
    if best[1] <= 0:
        # Default: chat-like prompts → chat, else text
        if "?" in text or text.startswith(("hi", "hello", "hey")):
            return "chat", 0.55, ["default=chat"]
        return "text", 0.5, ["default=text"]

    confidence = min(0.98, 0.55 + best[1] * 0.12)
    return best[0], round(confidence, 3), notes[:12]
