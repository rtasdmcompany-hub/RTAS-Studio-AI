"""Encrypted memory storage (HMAC-authenticated keystream cipher)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os


def _derive_key(secret: str | None = None) -> bytes:
    raw = (secret or os.environ.get("RTAS_MEMORY_SECRET") or "rtas-memory-v1").encode(
        "utf-8"
    )
    return hashlib.sha256(raw).digest()


def encrypt_text(plaintext: str, *, secret: str | None = None) -> str:
    key = _derive_key(secret)
    data = plaintext.encode("utf-8")
    # Counter-mode keystream from HMAC-SHA256
    out = bytearray()
    counter = 0
    while len(out) < len(data):
        block = hmac.new(key, counter.to_bytes(8, "big"), hashlib.sha256).digest()
        out.extend(block)
        counter += 1
    cipher = bytes(a ^ b for a, b in zip(data, out[: len(data)]))
    tag = hmac.new(key, cipher, hashlib.sha256).digest()[:16]
    return base64.urlsafe_b64encode(tag + cipher).decode("ascii")


def decrypt_text(token: str, *, secret: str | None = None) -> str:
    key = _derive_key(secret)
    raw = base64.urlsafe_b64decode(token.encode("ascii"))
    tag, cipher = raw[:16], raw[16:]
    expected = hmac.new(key, cipher, hashlib.sha256).digest()[:16]
    if not hmac.compare_digest(tag, expected):
        raise ValueError("Memory integrity check failed")
    out = bytearray()
    counter = 0
    while len(out) < len(cipher):
        block = hmac.new(key, counter.to_bytes(8, "big"), hashlib.sha256).digest()
        out.extend(block)
        counter += 1
    plain = bytes(a ^ b for a, b in zip(cipher, out[: len(cipher)]))
    return plain.decode("utf-8")
