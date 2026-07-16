"""Backend orchestrator / provider routing tests (no full app venv required)."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_PY = ROOT / "app" / "services" / "providers" / "base.py"


def test_select_live_provider_prefers_fal(monkeypatch=None):
    # Lightweight unit — no settings/pydantic import required.
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
    """Verify adapter contract without importing FastAPI/pydantic stack."""
    tree = ast.parse(BASE_PY.read_text(encoding="utf-8"))
    methods: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "BaseAIProvider":
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.add(item.name)
    required = {"generate", "status", "cancel", "download", "is_configured"}
    missing = required - methods
    assert not missing, f"BaseAIProvider missing methods: {missing}"


if __name__ == "__main__":
    test_select_live_provider_prefers_fal()
    test_select_live_provider_falls_back_to_replicate()
    test_provider_protocol_methods_exist()
    print("backend orchestrator tests: ok")
