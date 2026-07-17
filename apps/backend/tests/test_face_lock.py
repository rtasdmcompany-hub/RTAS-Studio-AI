"""Phase 5 Sprint 2 — AI Face Lock & Identity Engine tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FL = ROOT / "app" / "services" / "face_lock"
CG = ROOT / "app" / "services" / "character_generation"

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


def _load_pkg(pkg_name: str, pkg_path: Path, modules: list[tuple[str, str]]):
    _ensure_parents(pkg_name)
    if pkg_name in sys.modules and all(
        f"{pkg_name}.{mod_name}" in sys.modules for mod_name, _ in modules
    ):
        return
    pkg = type(sys)(pkg_name)
    pkg.__path__ = [str(pkg_path)]
    sys.modules[pkg_name] = pkg
    for mod_name, file_name in modules:
        _load(f"{pkg_name}.{mod_name}", pkg_path / file_name)


_load_pkg(
    "app.services.character_generation",
    CG,
    [
        ("version", "version.py"),
        ("models", "models.py"),
        ("templates", "templates.py"),
        ("validation", "validation.py"),
        ("paddle_status", "paddle_status.py"),
        ("registry", "registry.py"),
        ("store", "store.py"),
        ("engine", "engine.py"),
    ],
)

# Wire package exports so face_lock can resolve characters via package import.
_cg_pkg = sys.modules["app.services.character_generation"]
_cg_engine_mod = sys.modules["app.services.character_generation.engine"]
_cg_pkg.get_character = _cg_engine_mod.get_character
_cg_pkg.registry = sys.modules["app.services.character_generation.registry"]
_cg_pkg.store = sys.modules["app.services.character_generation.store"]

_load_pkg(
    "app.services.face_lock",
    FL,
    [
        ("version", "version.py"),
        ("models", "models.py"),
        ("embeddings", "embeddings.py"),
        ("references", "references.py"),
        ("identity", "identity.py"),
        ("validator", "validator.py"),
        ("store", "store.py"),
        ("consistency", "consistency.py"),
        ("lock_manager", "lock_manager.py"),
        ("engine", "engine.py"),
    ],
)

cg_engine = sys.modules["app.services.character_generation.engine"]
cg_store = sys.modules["app.services.character_generation.store"]
cg_registry = sys.modules["app.services.character_generation.registry"]
cg_paddle = sys.modules["app.services.character_generation.paddle_status"]

version = sys.modules["app.services.face_lock.version"]
models = sys.modules["app.services.face_lock.models"]
store = sys.modules["app.services.face_lock.store"]
engine = sys.modules["app.services.face_lock.engine"]
embeddings = sys.modules["app.services.face_lock.embeddings"]
references = sys.modules["app.services.face_lock.references"]


def setup_function():
    store.clear()
    cg_store.clear()
    cg_registry.clear()


def test_version():
    assert version.ENGINE_VERSION == "1.0.0"
    assert version.PHASE == 5
    assert version.SPRINT == 2


def test_identity_persistence_and_embedding():
    char = cg_engine.create_character(
        name="Locked Lead",
        registry_slot="Character_A",
        gender="female",
        age=28,
        hairstyle="long_wavy",
    )
    cid = char.character.character_id
    locked = engine.lock_character(cid, reference_kind="stored")
    assert locked["state"] == "locked"
    ref1 = locked["face_embedding_ref"]
    assert ref1.startswith("embedding://")

    # Re-lock without regenerate — same embedding ref
    locked2 = engine.lock_character(cid, reference_kind="stored")
    assert locked2["face_embedding_ref"] == ref1
    assert locked2["embedding"]["regenerated"] is False

    identity = engine.get_identity(cid)
    assert identity is not None
    assert identity["face_embedding_ref"] == ref1
    for trait in models.PRESERVED_TRAITS:
        assert trait in identity["preserved_traits"]
    feats = identity["features"]
    assert feats["hairstyle"] == "long_wavy"
    assert feats["age"] == 28


def test_face_consistency_and_identity_score():
    char = cg_engine.create_character(name="Score Me", registry_slot="Character_B")
    cid = char.character.character_id
    engine.lock_character(cid)
    verified = engine.verify_identity(cid)
    assert verified["identity_score"] >= 90
    assert verified["passed"] is True
    assert verified["drift_detected"] is False
    assert verified["consistency"]["consistent"] is True


def test_identity_drift_detection():
    char = cg_engine.create_character(name="Drift Subject", registry_slot="Character_C")
    cid = char.character.character_id
    engine.lock_character(cid)
    drifted = engine.verify_identity(
        cid,
        feature_overrides={
            "hairstyle": "buzz_cut",
            "beard": "full_beard",
            "age": 55,
            "jawline": "square_heavy",
        },
    )
    assert drifted["drift_detected"] is True
    assert drifted["identity_score"] < 90
    assert len(drifted["drift_flags"]) >= 2
    traits = {f["trait"] for f in drifted["drift_flags"]}
    assert "hairstyle" in traits or "age" in traits


def test_reference_loading_kinds():
    char = cg_engine.create_character(name="Refs", registry_slot="Character_A")
    cid = char.character.character_id

    stored = engine.lock_character(cid, reference_kind="stored")
    assert stored["reference"]["kind"] == "stored"
    assert stored["reference"]["url"]

    uploaded = engine.lock_character(
        cid,
        reference_kind="uploaded",
        reference_url="https://cdn.example.com/faces/lead.png",
        regenerate_embedding=True,
    )
    assert uploaded["reference"]["kind"] == "uploaded"
    assert "cdn.example.com" in uploaded["reference"]["url"]
    assert uploaded["face_embedding_ref"].startswith("embedding://face/")

    generated = references.build_reference(cid, kind="generated")
    assert generated is not None
    loaded = references.load_reference_payload(generated)
    assert loaded["loaded"] is True
    assert loaded["usable_for_lock"] is True


def test_embedding_not_regenerated_by_default():
    emb1 = embeddings.build_face_embedding(
        character_id="c1", features_fingerprint="abc", reference_url="/r.png"
    )
    emb2 = embeddings.build_face_embedding(
        character_id="c1",
        features_fingerprint="CHANGED",
        reference_url="/other.png",
        regenerate=False,
        existing=emb1,
    )
    assert emb2.face_embedding_ref == emb1.face_embedding_ref
    assert emb2.regenerated is False
    emb3 = embeddings.build_face_embedding(
        character_id="c1",
        features_fingerprint="CHANGED",
        reference_url="/other.png",
        regenerate=True,
        existing=emb1,
    )
    assert emb3.regenerated is True
    assert emb3.face_embedding_ref != emb1.face_embedding_ref


def test_paddle_still_works():
    status = cg_paddle.paddle_status()
    assert status["secrets_exposed"] is False
    assert "env_presence" in status
    assert all(isinstance(v, bool) for v in status["env_presence"].values())
