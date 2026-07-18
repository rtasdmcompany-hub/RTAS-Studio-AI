"""Phase 6 Sprint 5 — AI Cost Optimization & Provider Intelligence Engine tests."""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CI = ROOT / "app" / "services" / "cost_intelligence"

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
    _ensure_parents("app.services.cost_intelligence")
    pkg = type(sys)("app.services.cost_intelligence")
    pkg.__path__ = [str(CI)]
    sys.modules["app.services.cost_intelligence"] = pkg
    for name in (
        "version",
        "models",
        "pricing",
        "store",
        "token_tracker",
        "credit_tracker",
        "budget",
        "analytics",
        "ranking",
        "reports",
        "optimizer",
        "monitoring",
        "engine",
    ):
        _load(f"app.services.cost_intelligence.{name}", CI / f"{name}.py")
    # Wire package exports
    eng = sys.modules["app.services.cost_intelligence.engine"]
    ver = sys.modules["app.services.cost_intelligence.version"]
    pkg.ENGINE_NAME = ver.ENGINE_NAME
    pkg.ENGINE_VERSION = ver.ENGINE_VERSION
    pkg.ENGINE_LABEL = ver.ENGINE_LABEL
    pkg.get_cost_engine = eng.get_cost_engine
    pkg.reset_engine = eng.reset_engine


_load_pkg()

version = sys.modules["app.services.cost_intelligence.version"]
pricing = sys.modules["app.services.cost_intelligence.pricing"]
ranking = sys.modules["app.services.cost_intelligence.ranking"]
engine_mod = sys.modules["app.services.cost_intelligence.engine"]


def setup_function():
    engine_mod.reset_engine()


def test_version_unit():
    assert version.ENGINE_VERSION == "1.0.0"
    assert version.PHASE == 6
    assert version.SPRINT == 5


def test_cost_calculator():
    cheap = pricing.calculate_cost("gemini", tokens=1000)
    expensive = pricing.calculate_cost("claude", tokens=1000)
    assert cheap.total_usd > 0
    assert expensive.total_usd >= cheap.total_usd
    assert cheap.credits > 0


def test_token_and_credit_trackers():
    eng = engine_mod.get_cost_engine()
    eng.record_usage("openai", kind="tokens", tokens=1500, latency_ms=200, success=True)
    eng.record_usage("elevenlabs", kind="voice", quantity=5.0, latency_ms=400)
    usage = eng.usage()
    assert usage["tokens"]["openai"] >= 1500
    assert usage["credits"]["total_credits"] > 0


def test_budget_manager():
    eng = engine_mod.get_cost_engine()
    eng.record_usage("openai", kind="request", tokens=500, cost_usd=1.5)
    cost = eng.cost_summary()
    assert cost["budgets"]
    assert cost["budgets"][0]["spent_daily_usd"] >= 1.5


def test_provider_usage_dimensions():
    eng = engine_mod.get_cost_engine()
    eng.record_usage("stability", kind="images", images=2, latency_ms=900)
    eng.record_usage("runpod", kind="videos", quantity=3.0, gpu_time_sec=3.0)
    eng.record_usage("fal", kind="request", storage_mb=10.0)
    analytics = eng.analytics()
    by = {p["provider"]: p for p in analytics["providers"]}
    assert by["stability"]["images"] >= 2
    assert by["runpod"]["videos"] >= 1
    assert by["runpod"]["gpu_time"] >= 3.0
    assert by["fal"]["storage"] >= 10.0


def test_dynamic_ranking():
    eng = engine_mod.get_cost_engine()
    # Bias: make openai fail and gemini succeed cheaply
    for _ in range(5):
        eng.record_usage("openai", kind="tokens", tokens=1000, latency_ms=800, success=False)
        eng.record_usage("gemini", kind="tokens", tokens=1000, latency_ms=200, success=True)
    ranked = eng.ranking(capability="text")
    assert ranked["ranking"]
    assert ranked["top_provider"]
    providers = [r["provider"] for r in ranked["ranking"]]
    assert "gemini" in providers
    # Factors present
    top = ranked["ranking"][0]
    for key in (
        "cost_score",
        "speed_score",
        "availability_score",
        "quality_score",
        "reliability_score",
        "success_rate",
        "error_rate",
    ):
        assert key in top


def test_automatic_optimization():
    eng = engine_mod.get_cost_engine()
    result = eng.optimize(mode="cost", capability="text", tokens=2000)
    opt = result["optimization"]
    assert opt["selected_provider"]
    assert opt["estimated_cost_usd"] >= 0
    assert opt["savings_usd"] >= 0
    assert opt["ranking"]
    # Cost mode should prefer cheaper providers
    cost_opt = eng.optimize(mode="cost", capability="image", images=1)
    quality_opt = eng.optimize(mode="quality", capability="image", images=1)
    assert cost_opt["optimization"]["selected_provider"]
    assert quality_opt["optimization"]["selected_provider"]


def test_usage_reports():
    eng = engine_mod.get_cost_engine()
    eng.record_usage("openai", kind="tokens", tokens=100, project_id="proj_a", team_id="team_1")
    eng.record_usage("gemini", kind="tokens", tokens=200, project_id="proj_a", team_id="team_1")
    usage = eng.usage(project_id="proj_a", team_id="team_1", period="daily")
    assert usage["reports"]["daily"]["total_requests"] >= 2
    assert usage["project_report"]["scope_id"] == "proj_a"
    assert usage["team_report"]["scope_id"] == "team_1"
    assert usage["reports"]["monthly"]["period"] == "monthly"


def test_performance_monitoring():
    eng = engine_mod.get_cost_engine()
    eng.record_usage("openai", kind="tokens", tokens=100, latency_ms=120, project_id="p1")
    eng.record_usage("openai", kind="tokens", tokens=100, latency_ms=180, success=False, project_id="p1")
    analytics = eng.analytics()
    perf = analytics["performance"]
    assert "average_response_time_ms" in perf
    assert "cost_per_request" in perf
    assert "cost_per_project" in perf
    assert "success_rate" in perf
    assert "failure_rate" in perf
    assert "provider_uptime" in perf
    assert "queue_efficiency" in perf
    assert "p1" in perf["cost_per_project"]


def test_load_testing_500_usage_events():
    eng = engine_mod.get_cost_engine()
    providers = ("openai", "gemini", "claude", "stability", "elevenlabs", "runpod", "fal", "replicate")
    t0 = time.perf_counter()
    for i in range(500):
        p = providers[i % len(providers)]
        eng.record_usage(
            p,
            kind="tokens",
            tokens=100 + (i % 50),
            latency_ms=50 + (i % 200),
            success=(i % 17) != 0,
            project_id=f"proj_{i % 10}",
            team_id=f"team_{i % 5}",
        )
    elapsed = time.perf_counter() - t0
    analytics = eng.analytics()
    assert analytics["aggregate"]["requests"] >= 500
    assert elapsed < 5.0
    eps = 500 / elapsed if elapsed > 0 else 0
    assert eps > 50
    # Optimize under load still works
    opt = eng.optimize(mode="balanced", tokens=1000)
    assert opt["optimization"]["selected_provider"]
    ranked = ranking.rank_providers()
    assert len(ranked) == 8
