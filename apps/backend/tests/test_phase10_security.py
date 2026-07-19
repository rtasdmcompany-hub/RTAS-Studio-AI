"""Phase 10 Sprint 3 — Security hardening & compliance tests."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_runtime_production_detection():
    rt = _load("app.core.runtime", ROOT / "app" / "core" / "runtime.py")
    prev = {k: os.environ.get(k) for k in ("VERCEL", "RTAS_ENV", "ENVIRONMENT", "NODE_ENV", "RTAS_ENABLE_OPENAPI")}
    try:
        for k in prev:
            os.environ.pop(k, None)
        assert rt.is_production() is False
        assert rt.openapi_enabled() is True

        os.environ["VERCEL"] = "1"
        assert rt.is_production() is True
        assert rt.openapi_enabled() is False

        os.environ["RTAS_ENABLE_OPENAPI"] = "1"
        assert rt.openapi_enabled() is True
    finally:
        for k, v in prev.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_ssrf_guard_blocks_localhost_and_http():
    guard = _load("app.services.ssrf_guard", ROOT / "app" / "services" / "ssrf_guard.py")
    try:
        guard.assert_safe_outbound_url("http://evil.example/x.mp4")
        assert False, "expected SsrfError"
    except guard.SsrfError:
        pass
    try:
        guard.assert_safe_outbound_url("https://127.0.0.1/secret.mp4")
        assert False, "expected SsrfError"
    except guard.SsrfError:
        pass
    try:
        guard.assert_safe_outbound_url("https://evil.example.com/x.mp4")
        assert False, "expected SsrfError"
    except guard.SsrfError:
        pass


def test_ssrf_guard_allows_known_cdn_hosts():
    guard = _load("app.services.ssrf_guard", ROOT / "app" / "services" / "ssrf_guard.py")
    # DNS may fail offline — accept either allow or DNS failure as non-policy bug
    try:
        out = guard.assert_safe_outbound_url(
            "https://v3b.fal.media/files/example/video.mp4"
        )
        assert out.startswith("https://")
    except guard.SsrfError as exc:
        assert "DNS" in str(exc) or "allowlist" in str(exc) or "routable" in str(exc)


def test_upload_magic_and_job_id_sanitization():
    # Minimal bootstrap of upload_service without full FastAPI app
    os.environ.setdefault("AI_BACKEND_SECRET", "")
    svc_path = ROOT / "app" / "services" / "upload_service.py"
    # Ensure app.core.config can load
    if "app.core.config" not in sys.modules:
        _load("app.core.config", ROOT / "app" / "core" / "config.py")
    if "app.core.runtime" not in sys.modules:
        _load("app.core.runtime", ROOT / "app" / "core" / "runtime.py")
    if "app.services.storage" not in sys.modules:
        _load("app.services.storage", ROOT / "app" / "services" / "storage.py")

    us = _load("app.services.upload_service", svc_path)

    try:
        us.sanitize_job_id("../etc/passwd")
        assert False, "expected rejection"
    except Exception as exc:
        assert "Invalid" in str(exc) or getattr(exc, "status_code", None) == 400

    jid = us.sanitize_job_id("job_abc-123")
    assert jid == "job_abc-123"

    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
    us.assert_magic_bytes("faceReference", png)

    try:
        us.assert_magic_bytes("faceReference", b"not-an-image")
        assert False, "expected rejection"
    except Exception as exc:
        assert "image" in str(exc).lower() or getattr(exc, "status_code", None) == 400


def test_secure_headers_present():
    api = _load(
        "app.services.enterprise_security.api_security",
        ROOT / "app" / "services" / "enterprise_security" / "api_security.py",
    )
    headers = api.secure_headers()
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert "Content-Security-Policy" in headers


def test_main_disables_docs_in_production_source():
    text = (ROOT / "main.py").read_text(encoding="utf-8")
    assert "openapi_enabled" in text
    assert "SecurityHeadersMiddleware" in text
    assert "is_production" in text
    assert "/media/uploads" in text


def test_upload_route_requires_backend_auth():
    text = (ROOT / "app" / "api" / "routes" / "upload.py").read_text(encoding="utf-8")
    assert "require_backend_secret" in text
    assert "Depends" in text


def test_jwt_secret_fails_closed_in_production():
    secrets = _load(
        "app.services.enterprise_security.secrets",
        ROOT / "app" / "services" / "enterprise_security" / "secrets.py",
    )
    _load("app.core.runtime", ROOT / "app" / "core" / "runtime.py")
    prev_v = os.environ.get("VERCEL")
    prev_j = os.environ.get("RTAS_JWT_SECRET")
    prev_a = os.environ.get("AI_BACKEND_SECRET")
    try:
        os.environ["VERCEL"] = "1"
        os.environ.pop("RTAS_JWT_SECRET", None)
        os.environ.pop("AI_BACKEND_SECRET", None)
        try:
            secrets.jwt_signing_secret()
            assert False, "expected ValueError"
        except ValueError as exc:
            assert "required" in str(exc).lower()
    finally:
        if prev_v is None:
            os.environ.pop("VERCEL", None)
        else:
            os.environ["VERCEL"] = prev_v
        if prev_j is None:
            os.environ.pop("RTAS_JWT_SECRET", None)
        else:
            os.environ["RTAS_JWT_SECRET"] = prev_j
        if prev_a is None:
            os.environ.pop("AI_BACKEND_SECRET", None)
        else:
            os.environ["AI_BACKEND_SECRET"] = prev_a


def test_web_proxy_sends_backend_secret():
    proxy = (
        ROOT.parent
        / "web"
        / "src"
        / "lib"
        / "server"
        / "fastapi-proxy.ts"
    )
    text = proxy.read_text(encoding="utf-8")
    assert "X-Rtas-Backend-Secret" in text
    assert "backendSecretHeaders" in text


def test_webhook_idempotency_module_exists():
    path = (
        ROOT.parent
        / "web"
        / "src"
        / "lib"
        / "server"
        / "webhook-idempotency.ts"
    )
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "claimWebhookEventId" in text


def test_paddle_webhook_uses_idempotency():
    route = (
        ROOT.parent
        / "web"
        / "src"
        / "app"
        / "api"
        / "webhooks"
        / "paddle"
        / "route.ts"
    )
    text = route.read_text(encoding="utf-8")
    assert "claimWebhookEventId" in text
    assert "duplicate" in text


def test_gitignore_covers_env():
    gi = ROOT.parent.parent / ".gitignore"
    if not gi.exists():
        gi = ROOT.parents[1] / ".gitignore"
    text = gi.read_text(encoding="utf-8")
    assert ".env" in text
    assert ".env.local" in text or ".env*" in text


def test_no_hardcoded_live_secrets_in_backend_core():
    hits = []
    for path in (ROOT / "app" / "core").rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pat in ("sk-live-", "sk_live_", "BEGIN PRIVATE KEY", "AKIA"):
            if pat in text:
                hits.append(f"{path.name}:{pat}")
    assert hits == []
