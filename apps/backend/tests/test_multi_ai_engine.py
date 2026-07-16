"""Sprint 7 — Multi AI Video Generation Engine tests (no live cloud calls)."""

from __future__ import annotations

import asyncio
import importlib.util
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SERVICES = ROOT / "app" / "services"
PROVIDERS = SERVICES / "providers"
MULTI = SERVICES / "multi_ai"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# Minimal stubs so specialty/registry can import without full app stack.
@dataclass
class _FakeSettings:
    fal_key: str | None = "test-fal-key"
    runway_api_key: str | None = None
    kling_api_key: str | None = "kling-key"
    google_veo_api_key: str | None = None
    hailuo_api_key: str | None = None
    pika_api_key: str | None = None
    luma_api_key: str | None = None
    svd_api_key: str | None = None
    cogvideo_api_key: str | None = None
    replicate_api_token: str | None = None
    comfyui_api_url: str | None = None
    comfyui_api_key: str | None = None
    diffusers_enabled: bool = False
    fal_configured: bool = True
    replicate_configured: bool = False


class _FakeConfigMod:
    settings = _FakeSettings()

    @staticmethod
    def reload_settings():
        return _FakeConfigMod.settings


sys.modules["app.core.config"] = _FakeConfigMod()  # type: ignore

contracts = _load("app.services.providers.contracts", PROVIDERS / "contracts.py")
sys.modules["app.services.providers.contracts"] = contracts
base = _load("app.services.providers.base", PROVIDERS / "base.py")
sys.modules["app.services.providers.base"] = base


# Lightweight fake fal gateway (no network)
class _FakeFalGateway:
    @staticmethod
    def fal_key_available():
        return True

    @staticmethod
    def apply_fal_key():
        return "test-fal-key"

    @staticmethod
    async def fal_subscribe_generate(*, provider_name, model_id, job, extra_arguments=None):
        return base.ProviderResult(
            provider=provider_name,
            success=True,
            remote_url=f"https://example.com/{provider_name}.mp4",
            external_job_id=f"{provider_name}-job-1",
            metadata={"model_id": model_id, "gateway": "fal"},
        )

    @staticmethod
    async def fal_status_stub(provider_name, external_job_id):
        return base.ProviderStatus(
            provider=provider_name,
            external_job_id=external_job_id,
            status="completed",
            progress_percent=100,
        )


sys.modules["app.services.providers.fal_gateway"] = _FakeFalGateway()  # type: ignore
specialty = _load("app.services.providers.specialty", PROVIDERS / "specialty.py")
sys.modules["app.services.providers.specialty"] = specialty


# Stub legacy providers
class _StubProvider(base.BaseAIProvider):
    def __init__(self, name: str, configured: bool = False, succeed: bool = True):
        self.name = name
        self.display_name = name.title()
        self._configured = configured
        self._succeed = succeed
        self.cost_per_second_usd = 0.05
        self.typical_eta_seconds = 60
        self.strengths = ("cinematic",)

    def is_configured(self) -> bool:
        return self._configured

    async def generate(self, job):
        if not self._configured:
            return base.ProviderResult(
                provider=self.name, success=False, error="not configured"
            )
        if not self._succeed:
            return base.ProviderResult(
                provider=self.name, success=False, error="forced failure"
            )
        return base.ProviderResult(
            provider=self.name,
            success=True,
            remote_url=f"https://example.com/{self.name}.mp4",
            external_job_id=f"{self.name}-1",
        )


for mod_name, cls_name, configured in [
    ("fal", "FalProvider", True),
    ("replicate", "ReplicateProvider", False),
    ("comfyui", "ComfyUIProvider", False),
    ("diffusers_local", "DiffusersInstantIDProvider", False),
]:
    m = type(sys)(f"app.services.providers.{mod_name}")
    setattr(
        m,
        cls_name,
        lambda configured=configured, name=mod_name.split("_")[0]: _StubProvider(
            name if name != "diffusers" else "diffusers", configured=configured
        ),
    )
    # Fix: need proper class factories
sys.modules["app.services.providers.fal"] = type(sys)("fal")
sys.modules["app.services.providers.fal"].FalProvider = lambda: _StubProvider("fal", True)
sys.modules["app.services.providers.replicate"] = type(sys)("replicate")
sys.modules["app.services.providers.replicate"].ReplicateProvider = lambda: _StubProvider(
    "replicate", False
)
sys.modules["app.services.providers.comfyui"] = type(sys)("comfyui")
sys.modules["app.services.providers.comfyui"].ComfyUIProvider = lambda: _StubProvider(
    "comfyui", False
)
sys.modules["app.services.providers.diffusers_local"] = type(sys)("diffusers_local")
sys.modules[
    "app.services.providers.diffusers_local"
].DiffusersInstantIDProvider = lambda: _StubProvider("diffusers", False)

# Load multi_ai package
multi_pkg = type(sys)("app.services.multi_ai")
multi_pkg.__path__ = [str(MULTI)]
sys.modules["app.services.multi_ai"] = multi_pkg
for name, file_name in [
    ("models", "models.py"),
    ("registry", "registry.py"),
    ("selector", "selector.py"),
    ("queue", "queue.py"),
    ("engine", "engine.py"),
]:
    _load(f"app.services.multi_ai.{name}", MULTI / file_name)
_load("app.services.multi_ai", MULTI / "__init__.py")

engine_mod = sys.modules["app.services.multi_ai.engine"]
selector_mod = sys.modules["app.services.multi_ai.selector"]
registry_mod = sys.modules["app.services.multi_ai.registry"]


@dataclass
class _Job:
    job_id: str = "job-test-1"
    duration_seconds: int = 5
    compiled_prompt: str = "A lonely man walks in the rain"
    main_prompt: str = "A lonely man walks in the rain"
    category: str = "story"
    fields: dict[str, str] = field(default_factory=dict)


def test_provider_contract_methods():
    kling = specialty.KlingProvider()
    assert kling.is_configured()  # kling key or fal
    cost = kling.cost_estimate(10)
    assert cost.estimated_usd > 0
    eta = kling.eta(10)
    assert eta.eta_seconds > 0
    health = asyncio.run(kling.health_check())
    assert health.configured is True
    assert "Generate" not in kling.name  # sanity
    for method in ("generate", "cancel", "status", "retry", "download", "health_check"):
        assert hasattr(kling, method)


def test_detect_and_select():
    registry = registry_mod.build_provider_registry()
    available = registry_mod.detect_available_providers(registry)
    assert "fal" in available
    assert "kling" in available  # fal key + fal model OR kling key
    best = selector_mod.select_best_provider(
        registry, available=available, category="Movie Scene", mood="Emotional"
    )
    assert best in available
    chain = selector_mod.build_failover_chain(best, available, max_providers=4)
    assert best in chain
    assert len(chain) >= 1


def test_failover_flow():
    # Build engine with fal that fails then kling that succeeds
    registry = {
        "fal": _StubProvider("fal", configured=True, succeed=False),
        "kling": _StubProvider("kling", configured=True, succeed=True),
        "runway": _StubProvider("runway", configured=False),
    }
    eng = engine_mod.MultiAIVideoEngine(registry=registry)
    flow = asyncio.run(eng.generate_with_failover(_Job()))
    assert flow.success is True
    assert flow.provider == "kling"
    assert "fal" in flow.attempted_providers
    assert flow.queue_job.state == "completed"
    print("example_generation_flow=")
    print(flow.to_dict())


def test_compatibility_matrix():
    rows = registry_mod.provider_compatibility_matrix()
    names = {r["provider"] for r in rows}
    for required in (
        "veo",
        "runway",
        "kling",
        "hailuo",
        "pika",
        "luma",
        "svd",
        "cogvideo",
        "fal",
        "replicate",
    ):
        assert required in names


if __name__ == "__main__":
    test_provider_contract_methods()
    test_detect_and_select()
    test_failover_flow()
    test_compatibility_matrix()
    print("multi ai engine tests: ok")
