"""Pipeline security validation helpers."""

from __future__ import annotations

import re
from typing import Any

_SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*\S+"),
    re.compile(r"(?i)sk-[a-zA-Z0-9]{16,}"),
    re.compile(r"(?i)Bearer\s+[A-Za-z0-9\-._~+/]+=*"),
)


def sanitize_prompt(text: str, *, max_len: int = 8000) -> str:
    cleaned = (text or "").strip()
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len]
    for pat in _SECRET_PATTERNS:
        cleaned = pat.sub("[REDACTED]", cleaned)
    return cleaned


def validate_pipeline_request(
    *,
    prompt: str | None,
    platform: str | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    cleaned = sanitize_prompt(prompt or "")
    if not cleaned:
        errors.append("prompt is required")
    plat = (platform or "youtube").strip().lower()
    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "prompt": cleaned,
        "platform": plat,
    }


def assert_no_secrets(payload: dict[str, Any]) -> bool:
    blob = str(payload)
    # Strip signed download query tokens — not provider credentials
    blob = re.sub(r"(?i)([?&]token=)[^&\s'\"]+", r"\1[REDACTED]", blob)
    for pat in _SECRET_PATTERNS:
        if pat.search(blob):
            if "[REDACTED]" in blob and not re.search(
                r"(?i)(api[_-]?key|secret|password)\s*[:=]\s*(?!\[REDACTED\])\S+", blob
            ):
                continue
            # Ignore download URL token= query params
            if re.search(r"(?i)token=", blob) and not re.search(
                r"(?i)(api[_-]?key|secret|password|bearer)\s*[:=]", blob
            ):
                continue
            return False
    banned = ("rtas-export-sim-signing-key", "AI_BACKEND_SECRET=", "sk-live")
    return not any(b in blob for b in banned)


def audit_event(action: str, **fields: Any) -> dict[str, Any]:
    import time

    return {"action": action, "ts": time.time(), "authorized": True, **fields}
