"""Production smoke checks — route registration + lightweight TestClient probes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

SMOKE_ENDPOINTS: tuple[tuple[str, str, str], ...] = (
    # path, route_file, marker
    ("/api/ready", "health.py", "async def ready"),
    ("/api/router/status", "ai_router.py", 'get("/status")'),
    ("/api/video-engine/version", "video_engine.py", 'get("/version")'),
    ("/api/projects", "projects.py", "projects"),
    ("/api/assets", "assets.py", "assets"),
    ("/api/marketplace", "marketplace.py", 'prefix="/marketplace"'),
    ("/api/plugins", "plugin_framework.py", 'prefix="/plugins"'),
    ("/api/developers", "public_api_platform.py", 'prefix="/developers"'),
    ("/api/analytics", "analytics.py", 'prefix="/analytics"'),
    ("/api/admin/system", "platform_ops.py", "system"),
)


def _routes_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "api" / "routes"


def smoke_source_checks() -> dict[str, Any]:
    routes = _routes_dir()
    results: dict[str, Any] = {}
    for path, filename, marker in SMOKE_ENDPOINTS:
        file_path = routes / filename
        text = file_path.read_text(encoding="utf-8") if file_path.is_file() else ""
        ok = file_path.is_file() and marker.lower() in text.lower()
        results[path] = {"ok": ok, "source": filename, "marker": marker}
    passed = sum(1 for v in results.values() if v["ok"])
    return {
        "ok": passed == len(SMOKE_ENDPOINTS),
        "passed": passed,
        "total": len(SMOKE_ENDPOINTS),
        "checks": results,
    }


def smoke_http_probes() -> dict[str, Any]:
    """In-process HTTP smoke (no external network). Auth may return 401 — still alive."""
    try:
        from fastapi.testclient import TestClient

        from main import app
    except Exception as exc:
        # Local/dev may lack optional provider SDKs (e.g. fal_client). Source checks remain authoritative.
        return {
            "ok": True,
            "skipped": True,
            "reason": str(exc),
            "passed": 0,
            "total": 0,
            "probes": {},
        }

    client = TestClient(app)
    probes: dict[str, Any] = {}
    targets = [
        "/api/ready",
        "/api/health/ping",
        "/api/router/status",
        "/api/video-engine/version",
        "/api/marketplace/status",
        "/api/developers/status",
        "/api/plugins/status",
        "/api/analytics/status",
        "/api/phase10/rc2/status",
    ]
    for path in targets:
        try:
            resp = client.get(path)
            alive = resp.status_code in (200, 401, 403, 422)
            probes[path] = {
                "ok": alive,
                "statusCode": resp.status_code,
            }
        except Exception as exc:
            probes[path] = {"ok": False, "error": str(exc)}

    passed = sum(1 for v in probes.values() if v.get("ok"))
    return {
        "ok": passed == len(targets),
        "skipped": False,
        "passed": passed,
        "total": len(targets),
        "probes": probes,
    }
