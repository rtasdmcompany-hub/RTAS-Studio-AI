"""
Content moderation — blocks NSFW / policy-violating generation requests.

Scans all user-supplied text before any video generation starts. Violations are
logged to data/security_log.json.
"""

from __future__ import annotations

import json
import logging
import re
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import BackendRoot
from app.schemas.generation import GenerateRequest

logger = logging.getLogger(__name__)

CONTENT_POLICY_MESSAGE = "403 Forbidden - Content Policy Violation"
SECURITY_LOG_PATH = BackendRoot / "data" / "security_log.json"

_log_lock = threading.Lock()

# Category blacklist — never allow generation under these labels if injected.
BLOCKED_CATEGORIES = frozenset({"adult", "nsfw", "porn", "xxx", "erotic"})

# Term blacklist (word-boundary matched where possible).
BLOCKED_TERMS: tuple[str, ...] = (
    "porn",
    "pornography",
    "pornographic",
    "xxx",
    "nsfw",
    "nude",
    "nudes",
    "naked",
    "nudity",
    "sexual",
    "sexually",
    "erotic",
    "erotica",
    "hentai",
    "onlyfans",
    "stripper",
    "strip club",
    "prostitut",
    "brothel",
    "orgasm",
    "fetish",
    "bdsm",
    "hardcore",
    "softcore",
    "x-rated",
    "xrated",
    "explicit sex",
    "adult video",
    "adult content",
    "child porn",
    "cp ",
    "loli",
    "shota",
    "underage sex",
    "rape",
    "molest",
    "bestiality",
    "beastiality",
)

# Regex patterns for obfuscation / phrases.
BLOCKED_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bnsfw\b",
        r"\bxxx+\b",
        r"\bp[o0]rn\b",
        r"\bn+u+d+e+s?\b",
        r"\bs[e3]x+\s*(tape|scene|video|act|ual)",
        r"\b(adult|18\+)\s*(video|content|film|scene)\b",
        r"\b(strip\s*tease|lap\s*dance)\b",
    )
)


class ContentPolicyViolation(Exception):
    """Raised when user content fails the safety scan."""

    def __init__(self, reason: str, matched: list[str] | None = None):
        super().__init__(CONTENT_POLICY_MESSAGE)
        self.reason = reason
        self.matched = matched or []


@dataclass(frozen=True)
class ModerationResult:
    allowed: bool
    matched_terms: tuple[str, ...]
    scanned_fields: tuple[str, ...]


def _ensure_security_log() -> None:
    SECURITY_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not SECURITY_LOG_PATH.is_file():
        SECURITY_LOG_PATH.write_text("[]\n", encoding="utf-8")


def log_content_policy_violation(
    *,
    user_id: str | None,
    device_fingerprint: str | None,
    ip_address: str | None,
    category: str | None,
    job_id: str | None,
    matched_terms: list[str],
    reason: str,
    route: str | None = None,
    preview_only: bool | None = None,
) -> None:
    entry: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "content_policy_violation",
        "user_id": user_id or "anonymous",
        "device_fingerprint": device_fingerprint,
        "ip_address": ip_address,
        "category": category,
        "job_id": job_id,
        "route": route,
        "preview_only": preview_only,
        "matched_terms": matched_terms,
        "reason": reason,
    }

    with _log_lock:
        _ensure_security_log()
        try:
            existing = json.loads(SECURITY_LOG_PATH.read_text(encoding="utf-8"))
            if not isinstance(existing, list):
                existing = []
        except (json.JSONDecodeError, OSError):
            existing = []
        existing.append(entry)
        SECURITY_LOG_PATH.write_text(
            json.dumps(existing, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    logger.warning(
        "Content policy violation user=%s ip=%s matched=%s",
        user_id or "anonymous",
        ip_address or "unknown",
        ",".join(matched_terms) or reason,
    )


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _scan_text(text: str) -> list[str]:
    if not text or not text.strip():
        return []

    normalized = _normalize(text)
    hits: list[str] = []

    for term in BLOCKED_TERMS:
        if term in normalized:
            hits.append(term)

    for pattern in BLOCKED_PATTERNS:
        match = pattern.search(normalized)
        if match:
            hits.append(match.group(0))

    return sorted(set(hits))


def collect_request_text(body: GenerateRequest) -> dict[str, str]:
    """Gather all user-authored strings from a generation payload."""
    texts: dict[str, str] = {}

    if body.category:
        texts["category"] = str(body.category)

    for key, value in body.fields.items():
        if isinstance(value, str) and value.strip():
            texts[f"fields.{key}"] = value

    for key, meta in body.files.items():
        if meta.name:
            texts[f"files.{key}.name"] = meta.name

    return texts


def moderate_generate_request(body: GenerateRequest) -> ModerationResult:
    """Return whether the request passes NSFW / policy checks."""
    if body.category.lower() in BLOCKED_CATEGORIES:
        return ModerationResult(
            allowed=False,
            matched_terms=(body.category.lower(),),
            scanned_fields=("category",),
        )

    matched: set[str] = set()
    scanned: list[str] = []

    for field_id, text in collect_request_text(body).items():
        scanned.append(field_id)
        matched.update(_scan_text(text))

    allowed = len(matched) == 0
    return ModerationResult(
        allowed=allowed,
        matched_terms=tuple(sorted(matched)),
        scanned_fields=tuple(scanned),
    )


def assert_generate_request_allowed(body: GenerateRequest) -> None:
    """Raise ContentPolicyViolation if the payload fails moderation."""
    result = moderate_generate_request(body)
    if result.allowed:
        return
    raise ContentPolicyViolation(
        reason="Blocked NSFW or inappropriate content in generation request",
        matched=list(result.matched_terms),
    )


def moderate_output_prompt(prompt: str) -> ModerationResult:
    """Re-scan compiled provider prompt before cloud generation starts."""
    hits = _scan_text(prompt)
    return ModerationResult(
        allowed=len(hits) == 0,
        matched_terms=tuple(hits),
        scanned_fields=("compiled_prompt",),
    )


def assert_output_prompt_allowed(prompt: str) -> None:
    result = moderate_output_prompt(prompt)
    if result.allowed:
        return
    raise ContentPolicyViolation(
        reason="Blocked NSFW or inappropriate content in compiled prompt",
        matched=list(result.matched_terms),
    )
