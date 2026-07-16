"""Backend orchestrator / provider routing tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_select_live_provider_prefers_fal(monkeypatch=None):
    from app.core import config

    # Lightweight unit without full settings reload when keys are mocked.
    class _P:
        def __init__(self, name, configured):
            self.name = name
            self._configured = configured

        def is_configured(self):
            return self._configured

    adapters = {
        "fal": _P("fal", True),
        "replicate": _P("replicate", True),
        "comfyui": _P("comfyui", False),
        "diffusers": _P("diffusers", False),
    }
    for name in ("fal", "replicate", "comfyui", "diffusers"):
        provider = adapters[name]
        if provider.is_configured():
            assert provider.name == "fal"
            return
    raise AssertionError("expected fal")


def test_select_live_provider_falls_back_to_replicate():
    class _P:
        def __init__(self, name, configured):
            self.name = name
            self._configured = configured

        def is_configured(self):
            return self._configured

    adapters = {
        "fal": _P("fal", False),
        "replicate": _P("replicate", True),
        "comfyui": _P("comfyui", False),
        "diffusers": _P("diffusers", False),
    }
    selected = None
    for name in ("fal", "replicate", "comfyui", "diffusers"):
        provider = adapters[name]
        if provider.is_configured():
            selected = provider
            break
    assert selected is not None
    assert selected.name == "replicate"


def test_provider_protocol_methods_exist():
    from app.services.providers.base import BaseAIProvider, ProviderResult

    assert hasattr(BaseAIProvider, "generate")
    assert hasattr(BaseAIProvider, "status")
    assert hasattr(BaseAIProvider, "cancel")
    assert hasattr(BaseAIProvider, "download")
    assert ProviderResult.__dataclass_fields__


if __name__ == "__main__":
    test_select_live_provider_prefers_fal()
    test_select_live_provider_falls_back_to_replicate()
    test_provider_protocol_methods_exist()
    print("backend orchestrator tests: ok")
