"""Phase 6 Sprint 1 — Multi AI Provider Orchestration Engine tests."""

from __future__ import annotations

import asyncio
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PO = ROOT / "app" / "services" / "provider_orchestration"

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
    _ensure_parents("app.services.provider_orchestration")
    if "app.services.provider_orchestration.manager" in sys.modules:
        return
    pkg = type(sys)("app.services.provider_orchestration")
    pkg.__path__ = [str(PO)]
    sys.modules["app.services.provider_orchestration"] = pkg
    for name in (
        "version",
        "models",
        "base",
        "priority",
        "registry",
        "builtins",
        "discovery",
        "health",
        "manager",
    ):
        _load(f"app.services.provider_orchestration.{name}", PO / f"{name}.py")


_load_pkg()

version = sys.modules["app.services.provider_orchestration.version"]
models = sys.modules["app.services.provider_orchestration.models"]
base = sys.modules["app.services.provider_orchestration.base"]
registry_mod = sys.modules["app.services.provider_orchestration.registry"]
priority = sys.modules["app.services.provider_orchestration.priority"]
discovery = sys.modules["app.services.provider_orchestration.discovery"]
manager_mod = sys.modules["app.services.provider_orchestration.manager"]
builtins = sys.modules["app.services.provider_orchestration.builtins"]


def setup_function():
    manager_mod.reset_provider_manager()


def test_version_unit():
    assert version.ENGINE_VERSION == "1.0.0"
    assert version.PHASE == 6
    assert version.SPRINT == 1
    assert "Orchestration" in version.ENGINE_NAME


def test_capability_and_status_models():
    assert "text" in models.ALL_CAPABILITIES
    assert "image" in models.ALL_CAPABILITIES
    assert "video" in models.ALL_CAPABILITIES
    assert "audio" in models.ALL_CAPABILITIES
    assert "music" in models.ALL_CAPABILITIES
    assert "voice" in models.ALL_CAPABILITIES
    assert "embedding" in models.ALL_CAPABILITIES
    assert "vision" in models.ALL_CAPABILITIES
    assert "translation" in models.ALL_CAPABILITIES
    assert set(models.ALL_STATUSES) == {
        "online",
        "offline",
        "busy",
        "disabled",
        "maintenance",
    }


def test_registry_registration():
    reg = registry_mod.ProviderRegistry()
    provider = builtins._StubProvider(
        "custom_ai",
        "Custom AI",
        ("text", "embedding"),
        60,
    )
    reg.register(provider)
    assert reg.has("custom_ai")
    assert reg.get("custom_ai") is provider
    assert reg.count() == 1
    assert reg.unregister("custom_ai") is True
    assert reg.count() == 0


def test_automatic_discovery():
    reg = registry_mod.ProviderRegistry()
    result = discovery.discover_providers(reg)
    assert result["installed_count"] >= 8
    assert "fal" in result["discovered"]
    assert "openai" in result["discovered"]
    assert "simulation" in result["discovered"]
    assert reg.has("gemini")
    assert reg.has("elevenlabs")


def test_priority_system():
    mgr = manager_mod.AIProviderManager(auto_discover=True)
    ordered = priority.sort_by_priority(mgr.registry.all())
    assert ordered[0].get_priority() <= ordered[-1].get_priority()
    # fal (15) should rank before simulation (100)
    ids = [p.provider_id for p in ordered]
    assert ids.index("fal") < ids.index("simulation")
    selected = mgr.select_provider("video")
    assert selected is not None
    assert selected.supports("video")


def test_health_monitoring():
    mgr = manager_mod.AIProviderManager(auto_discover=True)
    health = asyncio.run(mgr.health_monitor())
    assert health["total"] >= 8
    assert health["online"] >= 1
    assert len(health["reports"]) == health["total"]


def test_manager_list_installed_api_shape():
    mgr = manager_mod.get_provider_manager(refresh=True)
    payload = mgr.list_installed()
    assert payload["version"] == "1.0.0"
    assert payload["count"] >= 8
    assert payload["installed_providers"]
    first = payload["installed_providers"][0]
    assert "provider_id" in first
    assert "status" in first
    assert "capabilities" in first
    assert "version" in first
    assert set(payload["capabilities_catalog"]) == set(models.ALL_CAPABILITIES)


def test_provider_invoke_unified_interface():
    mgr = manager_mod.AIProviderManager(auto_discover=True)
    result = asyncio.run(mgr.invoke("Hello RTAS", capability="text", provider_id="simulation"))
    assert result["success"] is True
    assert result["provider"] == "simulation"


def test_disable_and_status_states():
    provider = builtins._StubProvider("temp", "Temp", ("text",), 90)
    provider.set_status("busy")
    assert provider.get_status() == "busy"
    provider.set_status("maintenance")
    assert provider.get_status() == "maintenance"
    provider.disable()
    assert provider.get_status() == "disabled"
    provider.enable()
    provider.set_status("online")
    assert provider.get_status() == "online"
