"""SSRF protection for outbound media fetches (provider CDN caching)."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

# Provider / CDN hosts we expect when caching generated MP4s.
_ALLOWED_HOST_SUFFIXES: tuple[str, ...] = (
    "fal.media",
    "fal.ai",
    "replicate.delivery",
    "replicate.com",
    "r2.dev",
    "cloudflarestorage.com",
    "amazonaws.com",
    "googleusercontent.com",
    "storage.googleapis.com",
)


class SsrfError(ValueError):
    pass


def _host_allowed(host: str) -> bool:
    h = host.lower().rstrip(".")
    if not h or h in {"localhost", "127.0.0.1", "0.0.0.0", "::1"}:
        return False
    try:
        ip = ipaddress.ip_address(h)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
        ):
            return False
        return True  # literal public IP — rare but allow for CDN edges
    except ValueError:
        pass
    return any(h == suf or h.endswith("." + suf) for suf in _ALLOWED_HOST_SUFFIXES)


def assert_safe_outbound_url(url: str) -> str:
    """Raise SsrfError if URL is not an allowed HTTPS provider/CDN target."""
    raw = (url or "").strip()
    if not raw:
        raise SsrfError("empty remote URL")
    parsed = urlparse(raw)
    if parsed.scheme != "https":
        raise SsrfError("only https outbound fetches are allowed")
    host = (parsed.hostname or "").lower()
    if not _host_allowed(host):
        raise SsrfError(f"host not in allowlist: {host}")
    # Block obvious credential-in-URL patterns
    if parsed.username or parsed.password:
        raise SsrfError("credentials in URL are not allowed")
    # Resolve DNS and reject private answers (DNS rebinding mitigation)
    try:
        infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise SsrfError(f"DNS resolution failed for {host}") from exc
    for info in infos:
        addr = info[4][0]
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            continue
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
        ):
            raise SsrfError(f"resolved address is not publicly routable: {addr}")
    return raw


def _configured_callback_hosts() -> set[str]:
    import os

    hosts: set[str] = set()
    for key in (
        "PUBLIC_BASE_URL",
        "NEXTAUTH_URL",
        "NEXT_PUBLIC_APP_URL",
        "VERCEL_URL",
        "RTAS_CALLBACK_ALLOW_HOSTS",
    ):
        raw = (os.environ.get(key) or "").strip()
        if not raw:
            continue
        if key == "RTAS_CALLBACK_ALLOW_HOSTS":
            for part in raw.split(","):
                h = part.strip().lower().removeprefix("https://").removeprefix("http://").split("/")[0]
                if h:
                    hosts.add(h)
            continue
        if "://" not in raw and key == "VERCEL_URL":
            hosts.add(raw.lower())
            continue
        try:
            host = (urlparse(raw if "://" in raw else f"https://{raw}").hostname or "").lower()
        except Exception:
            host = ""
        if host:
            hosts.add(host)
    # Common Vercel app suffixes for this project
    hosts.update(
        {
            "rtas-studio-ai-web.vercel.app",
            "rtas-studio-ai-api.vercel.app",
        }
    )
    return hosts


def assert_safe_callback_url(url: str, *, allow_localhost: bool = False) -> str:
    """Allowlist webhook/status callback URLs (Next.js app hosts only)."""
    raw = (url or "").strip()
    if not raw:
        raise SsrfError("empty callback URL")
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()
    if allow_localhost and host in {"localhost", "127.0.0.1"}:
        if parsed.scheme not in {"http", "https"}:
            raise SsrfError("invalid callback scheme")
        return raw
    if parsed.scheme != "https":
        raise SsrfError("only https callbacks are allowed")
    if parsed.username or parsed.password:
        raise SsrfError("credentials in URL are not allowed")
    allowed = _configured_callback_hosts()
    if host not in allowed and not any(host.endswith("." + h) for h in allowed):
        # Also allow *.vercel.app for preview deploys of this project
        if not (host.endswith(".vercel.app") and "rtas" in host):
            raise SsrfError(f"callback host not allowed: {host}")
    return raw
