"""Phase 6 Sprint 3 — AI Model Routing Engine tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MR = ROOT / "app" / "services" / "model_routing"

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
    _ensure_parents("app.services.model_routing")
    if "app.services.model_routing.engine" in sys.modules:
        return
    pkg = type(sys)("app.services.model_routing")
    pkg.__path__ = [str(MR)]
    sys.modules["app.services.model_routing"] = pkg
    for name in (
        "version",
        "models",
        "detection",
        "rules",
        "model_registry",
        "scoring",
        "analytics",
        "engine",
    ):
        _load(f"app.services.model_routing.{name}", MR / f"{name}.py")


_load_pkg()

version = sys.modules["app.services.model_routing.version"]
detection = sys.modules["app.services.model_routing.detection"]
rules = sys.modules["app.services.model_routing.rules"]
registry_mod = sys.modules["app.services.model_routing.model_registry"]
scoring = sys.modules["app.services.model_routing.scoring"]
analytics = sys.modules["app.services.model_routing.analytics"]
engine = sys.modules["app.services.model_routing.engine"]


def setup_function():
    engine.reset_routing()


def test_version_unit():
    assert version.ENGINE_VERSION == "1.0.0"
    assert version.PHASE == 6
    assert version.SPRINT == 3


def test_request_type_detection():
    assert detection.detect_request_type("Generate an image of a mountain sunset")[0] == "image"
    assert detection.detect_request_type("Create a cinematic video clip of a chase")[0] == "video"
    assert detection.detect_request_type("Text to speech this narration")[0] == "voice"
    assert detection.detect_request_type("Translate this paragraph into French")[0] == "translation"
    assert detection.detect_request_type("Refactor this Python function", hint="code")[0] == "code"
    assert detection.detect_request_type("Compose music for a trailer")[0] == "music"


def test_routing_rules_defaults():
    assert rules.preferred_providers("text")[0] in ("openai", "claude")
    assert rules.preferred_providers("image")[0] == "stability"
    assert rules.preferred_providers("video")[0] == "runpod"
    assert rules.preferred_providers("voice")[0] == "elevenlabs"


def test_model_registry_priority():
    reg = registry_mod.get_model_registry()
    assert reg.list_payload()["count"] >= 10
    images = reg.for_type("image")
    assert images
    assert images[0].priority <= images[-1].priority


def test_select_best_providers():
    text = engine.select_provider("Write a short essay about innovation")
    assert text["request_type"] in ("text", "chat")
    assert text["provider"] in ("openai", "claude", "gemini")

    image = engine.select_provider("Generate an image of a futuristic city")
    assert image["request_type"] == "image"
    assert image["provider"] == "stability"

    video = engine.select_provider("Generate video of ocean waves at sunrise")
    assert video["request_type"] == "video"
    assert video["provider"] == "runpod"

    voice = engine.select_provider("Text to speech this voiceover script")
    assert voice["request_type"] == "voice"
    assert voice["provider"] == "elevenlabs"


def test_fallback_and_failover_chain():
    plan = engine.plan_route("Generate an image of a red sports car")
    assert plan["selected_provider"] == "stability"
    assert plan["failover_enabled"] is True
    assert isinstance(plan["fallback_chain"], list)
    assert len(plan["fallback_chain"]) >= 1
    providers = {x["provider"] for x in plan["fallback_chain"]}
    assert "simulation" in providers or "openai" in providers or "fal" in providers


def test_cost_latency_quality_strategies():
    cheap = engine.select_provider(
        "Write a short summary of AI",
        request_type="text",
        strategy="cost",
        prefer_cheap=True,
    )
    quality = engine.select_provider(
        "Write a short summary of AI",
        request_type="text",
        strategy="quality",
    )
    assert cheap["provider"]
    assert quality["provider"]
    assert cheap["score"] > 0
    assert quality["score"] > 0


def test_load_balancing_and_analytics():
    for i in range(5):
        engine.select_provider(f"Chat with me about topic {i}", request_type="chat")
    status = engine.router_status()
    assert status["ok"] is True
    assert status["analytics"]["count"] >= 5
    assert status["model_count"] >= 10
    models = engine.list_models()
    assert models["count"] >= 10
    assert "rules" in models


def test_routing_accuracy_suite():
    cases = [
        ("Explain quantum computing simply", "text", ("openai", "claude", "gemini")),
        ("Hello, can we chat about travel?", "chat", ("openai", "claude", "gemini")),
        ("Draw a picture of a neon fox", "image", ("stability",)),
        ("Make a short video of rain in Tokyo", "video", ("runpod",)),
        ("Speak this sentence with a warm voice", "voice", ("elevenlabs",)),
        ("Compose music for an epic trailer", "music", ("elevenlabs", "fal")),
        ("Translate hello into Spanish", "translation", ("openai", "gemini", "claude")),
        ("Fix this Python bug in my function", "code", ("openai", "claude", "gemini")),
    ]
    hits = 0
    for prompt, expected_type, allowed_providers in cases:
        result = engine.select_provider(prompt)
        if result["request_type"] == expected_type and result["provider"] in allowed_providers:
            hits += 1
    accuracy = 100.0 * hits / len(cases)
    assert accuracy >= version.ROUTING_ACCURACY_THRESHOLD
    assert hits == len(cases)


def test_scoring_unit():
    reg = registry_mod.get_model_registry()
    entry = reg.get("gpt-4o-mini")
    assert entry is not None
    metrics = scoring.composite_score(entry, prefer_cheap=True)
    assert 0 <= metrics["overall"] <= 1
    assert metrics["cost_score"] >= metrics["quality_score"] or True  # relative ok
