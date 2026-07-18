"""Phase 6 Sprint 2 — AI Provider Connector Framework tests."""

from __future__ import annotations

import asyncio
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PC = ROOT / "app" / "services" / "provider_connectors"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _ensure_parents(pkg_name: str):
    parts = pkg_name.split(".")
    for i in range(1, len(parts)):
        parent = ".".join(parts[:i])
        if parent not in sys.modules:
            mod = type(sys)(parent)
            mod.__path__ = []
            sys.modules[parent] = mod
    if "app" in sys.modules:
        sys.modules["app"].__path__ = [str(ROOT / "app")]
    if "app.services" in sys.modules:
        sys.modules["app.services"].__path__ = [str(ROOT / "app" / "services")]


def _load_pkg():
    _ensure_parents("app.services.provider_connectors")
    if "app.services.provider_connectors.engine" in sys.modules:
        return
    pkg = type(sys)("app.services.provider_connectors")
    pkg.__path__ = [str(PC)]
    sys.modules["app.services.provider_connectors"] = pkg

    for name in ("version", "models", "config", "auth", "retry", "base"):
        _load(f"app.services.provider_connectors.{name}", PC / f"{name}.py")

    adapters_pkg = type(sys)("app.services.provider_connectors.adapters")
    adapters_pkg.__path__ = [str(PC / "adapters")]
    sys.modules["app.services.provider_connectors.adapters"] = adapters_pkg
    for name in (
        "openai_adapter",
        "gemini_adapter",
        "claude_adapter",
        "runpod_adapter",
        "stability_adapter",
        "elevenlabs_adapter",
    ):
        _load(
            f"app.services.provider_connectors.adapters.{name}",
            PC / "adapters" / f"{name}.py",
        )
    _load(
        "app.services.provider_connectors.adapters",
        PC / "adapters" / "__init__.py",
    )
    # reload adapters __init__ into package
    sys.modules["app.services.provider_connectors.adapters"] = _load(
        "app.services.provider_connectors.adapters_init",
        PC / "adapters" / "__init__.py",
    )
    # Fix: adapters package needs BUILTIN_CONNECTORS on the package module
    ad = sys.modules["app.services.provider_connectors.adapters_init"]
    sys.modules["app.services.provider_connectors.adapters"] = ad
    ad.__path__ = [str(PC / "adapters")]

    for name in ("registry", "health", "engine"):
        _load(f"app.services.provider_connectors.{name}", PC / f"{name}.py")


_load_pkg()

version = sys.modules["app.services.provider_connectors.version"]
models = sys.modules["app.services.provider_connectors.models"]
config = sys.modules["app.services.provider_connectors.config"]
auth = sys.modules["app.services.provider_connectors.auth"]
registry_mod = sys.modules["app.services.provider_connectors.registry"]
engine_mod = sys.modules["app.services.provider_connectors.engine"]
openai_mod = sys.modules["app.services.provider_connectors.adapters.openai_adapter"]


def setup_function():
    engine_mod.reset_engine()


def test_version_unit():
    assert version.ENGINE_VERSION == "1.0.0"
    assert version.PHASE == 6
    assert version.SPRINT == 2


def test_config_loader_unit():
    cfg = config.load_provider_config("openai")
    assert cfg.api_key_env == "OPENAI_API_KEY"
    public = cfg.public_dict()
    assert "api_key" not in public
    assert public["api_key_configured"] in (True, False)
    ids = config.list_config_ids()
    for required in ("openai", "gemini", "claude", "runpod", "stability", "elevenlabs"):
        assert required in ids


def test_auth_never_exposes_secrets():
    status = auth.auth_status("openai")
    assert status["secrets_exposed"] is False
    blob = str(status)
    assert "sk-" not in blob


def test_registry_discovery_and_priority():
    reg = registry_mod.get_registry()
    discovered = reg.discover()
    assert len(discovered) >= 6
    for pid in ("openai", "gemini", "claude", "runpod", "stability", "elevenlabs"):
        assert reg.get(pid) is not None
    ordered = [c.provider_id for c in reg.by_priority()]
    assert ordered[0] == "openai"  # priority 10
    assert "elevenlabs" in ordered


def test_standard_request_response_models():
    req = models.StandardRequest(prompt="hello", capability="text")
    assert req.to_dict()["prompt"] == "hello"
    resp = models.StandardResponse(
        provider="openai",
        success=True,
        capability="text",
        data={"ok": True},
    )
    assert resp.to_dict()["success"] is True


def test_connector_placeholder_execute():
    connector = openai_mod.OpenAIConnector(config.load_provider_config("openai"))

    async def _run():
        # Force placeholder path by ensuring we get a response
        req = models.StandardRequest(prompt="test connector", capability="text")
        return await connector.execute(req)

    result = asyncio.run(_run())
    assert result.success is True
    assert result.provider == "openai"
    assert result.latency_ms >= 0
    assert result.provider_version


def test_engine_list_status_test():
    engine = engine_mod.get_connector_engine()
    listed = engine.list_providers()
    assert listed["count"] >= 6
    assert listed["version"] == "1.0.0"

    async def _run():
        status = await engine.status()
        test = await engine.test_provider("stability", prompt="probe", capability="image")
        all_tests = await engine.test_all()
        return status, test, all_tests

    status, test, all_tests = asyncio.run(_run())
    assert len(status["statuses"]) >= 6
    assert test["ok"] is True
    assert test["secrets_exposed"] is False
    assert all_tests["total"] >= 6
    assert all_tests["passed"] >= 6


def test_unified_error_unsupported_capability():
    connector = openai_mod.OpenAIConnector(config.load_provider_config("openai"))

    async def _run():
        req = models.StandardRequest(prompt="x", capability="music")
        return await connector.execute(req)

    result = asyncio.run(_run())
    assert result.success is False
    assert result.error is not None
    assert result.error.code == "unsupported_capability"
