"""Phase 6 Sprint 6 — AI Memory, Context & Knowledge Engine tests."""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MK = ROOT / "app" / "services" / "memory_knowledge"

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
    _ensure_parents("app.services.memory_knowledge")
    pkg = type(sys)("app.services.memory_knowledge")
    pkg.__path__ = [str(MK)]
    sys.modules["app.services.memory_knowledge"] = pkg
    for name in (
        "version",
        "models",
        "crypto",
        "store",
        "security",
        "cache",
        "metrics",
        "retrieval",
        "memory_engine",
        "context_engine",
        "knowledge_engine",
        "engine",
    ):
        _load(f"app.services.memory_knowledge.{name}", MK / f"{name}.py")
    eng = sys.modules["app.services.memory_knowledge.engine"]
    ver = sys.modules["app.services.memory_knowledge.version"]
    pkg.ENGINE_NAME = ver.ENGINE_NAME
    pkg.ENGINE_VERSION = ver.ENGINE_VERSION
    pkg.ENGINE_LABEL = ver.ENGINE_LABEL
    pkg.get_memory_engine = eng.get_memory_engine
    pkg.reset_engine = eng.reset_engine


_load_pkg()

version = sys.modules["app.services.memory_knowledge.version"]
crypto = sys.modules["app.services.memory_knowledge.crypto"]
security = sys.modules["app.services.memory_knowledge.security"]
retrieval = sys.modules["app.services.memory_knowledge.retrieval"]
engine_mod = sys.modules["app.services.memory_knowledge.engine"]


def setup_function():
    engine_mod.reset_engine()


def test_version_unit():
    assert version.ENGINE_VERSION == "1.0.0"
    assert version.PHASE == 6
    assert version.SPRINT == 6


def test_encrypted_memory_storage():
    token = crypto.encrypt_text("secret character bible")
    assert token != "secret character bible"
    assert crypto.decrypt_text(token) == "secret character bible"


def test_memory_store_and_retrieve():
    eng = engine_mod.get_memory_engine()
    stored = eng.store(
        user_id="user_a",
        memory_type="character",
        title="Aria Captain",
        content="Aria is a calm starship captain with silver hair",
        project_id="proj_1",
        character_id="char_aria",
        tags=["character", "captain"],
    )
    assert stored["memory"]["memory_id"]
    assert stored["knowledge"]["knowledge_id"]
    got = eng.retrieve(user_id="user_a", query="starship captain", project_id="proj_1")
    assert got["count"] >= 1
    assert any("Aria" in (r.get("title") or "") for r in got["results"])


def test_memory_isolation_security():
    eng = engine_mod.get_memory_engine()
    eng.store(
        user_id="user_a",
        memory_type="prompt",
        title="private prompt",
        content="user a secret workflow",
        project_id="proj_a",
    )
    other = eng.retrieve(user_id="user_b", query="secret workflow")
    assert other["count"] == 0


def test_context_continuity():
    eng = engine_mod.get_memory_engine()
    ctx = eng.load_context(
        user_id="user_a",
        project_id="proj_story",
        prompt="Open with sunrise over desert",
        output="Wide establishing shot rendered",
        story={"act": 1, "theme": "hope"},
        character={"name": "Aria", "mood": "resolute"},
        scene={"location": "desert", "time": "dawn"},
        camera={"shot": "wide", "lens": "24mm"},
        audio={"bed": "wind ambience"},
        environment={"weather": "clear", "temp": "cool"},
        workflow={"step": "storyboard"},
    )
    assert ctx["context"]["previous_prompts"]
    assert ctx["reconstructed"]["story"]["theme"] == "hope"
    assert ctx["reconstructed"]["character"]["name"] == "Aria"
    assert ctx["context_accuracy"] > 0
    again = eng.load_context(
        user_id="user_a",
        project_id="proj_story",
        prompt="Track into close-up on Aria",
    )
    assert len(again["context"]["previous_prompts"]) == 2


def test_project_memory_and_history():
    eng = engine_mod.get_memory_engine()
    eng.store(
        user_id="u1",
        memory_type="project",
        title="Nebula Pilot",
        content="Sci-fi pilot episode about lost colony",
        project_id="proj_nebula",
    )
    eng.store(
        user_id="u1",
        memory_type="asset",
        title="Nebula HDRI",
        content="space nebula environment map",
        project_id="proj_nebula",
        asset_id="asset_hdri",
    )
    proj = eng.project("u1", "proj_nebula")
    assert proj["memory_count"] >= 2
    assert proj["by_type"]
    hist = eng.history(user_id="u1", project_id="proj_nebula")
    assert hist["count"] >= 1
    assert hist["history"]


def test_knowledge_search_and_smart_retrieval():
    eng = engine_mod.get_memory_engine()
    eng.store(
        user_id="u1",
        memory_type="character",
        title="Captain Aria",
        content="silver hair captain of the Orion vessel",
        project_id="p1",
        tags=["character"],
    )
    eng.store(
        user_id="u1",
        memory_type="prompt",
        title="Cinematic dawn",
        content="cinematic sunrise desert wide shot golden hour",
        project_id="p1",
        tags=["prompt", "style"],
    )
    eng.store(
        user_id="u1",
        memory_type="project",
        title="Orion Lost Colony",
        content="sci-fi project about Orion vessel and lost colony",
        project_id="p1",
    )
    eng.store(
        user_id="u1",
        memory_type="asset",
        title="Orion Bridge Set",
        content="bridge set asset for Orion vessel",
        project_id="p1",
    )
    ks = eng.knowledge_search(user_id="u1", query="Orion captain vessel")
    assert ks["count"] >= 1
    assert ks["character_recall"] is not None
    assert ks["prompt_suggestions"] is not None
    assert "similar_projects" in ks
    assert "duplicates" in ks


def test_duplicate_detection():
    a = "cinematic sunrise desert wide shot golden hour"
    b = "cinematic sunrise desert wide shot golden hour lighting"
    score = retrieval.jaccard(a, b)
    assert score > 0.5
    dups = retrieval.detect_duplicates(
        a,
        [{"id": "1", "title": "t", "body": b}],
        threshold=0.5,
    )
    assert dups


def test_access_control_requires_user():
    eng = engine_mod.get_memory_engine()
    try:
        eng.store(user_id="", memory_type="prompt", title="x", content="y")
        assert False, "expected AccessDenied"
    except security.AccessDenied:
        pass


def test_performance_metrics():
    eng = engine_mod.get_memory_engine()
    eng.store(user_id="u1", memory_type="prompt", title="p", content="neon city rain night", project_id="p9")
    eng.retrieve(user_id="u1", query="neon city")
    eng.knowledge_search(user_id="u1", query="neon rain")
    perf = eng.performance()
    assert "retrieval_time_ms" in perf
    assert "memory_size" in perf
    assert "cache_hit_rate" in perf
    assert "search_accuracy" in perf
    assert "context_accuracy" in perf
    assert "knowledge_index_health" in perf


def test_stress_store_retrieve_search():
    eng = engine_mod.get_memory_engine()
    t0 = time.perf_counter()
    for i in range(200):
        eng.store(
            user_id="stress_user",
            memory_type="prompt" if i % 2 == 0 else "scene",
            title=f"Scene {i} neon alley",
            content=f"production scene {i} with neon alley rain reflections character walk",
            project_id=f"proj_{i % 8}",
            tags=["stress", "scene"],
            index_knowledge=True,
        )
    for i in range(50):
        eng.retrieve(user_id="stress_user", query="neon alley rain", project_id=f"proj_{i % 8}")
        eng.knowledge_search(user_id="stress_user", query="neon alley character")
    elapsed = time.perf_counter() - t0
    perf = eng.performance()
    assert perf["memory_size"] >= 200
    assert elapsed < 15.0
    assert perf["retrieval_time_ms"] < 500
