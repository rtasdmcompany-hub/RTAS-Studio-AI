"""Phase 5 Sprint 3 — AI Character Style & Appearance Engine tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AP = ROOT / "app" / "services" / "appearance"
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

_cg_pkg = sys.modules["app.services.character_generation"]
_cg_engine_mod = sys.modules["app.services.character_generation.engine"]
_cg_pkg.get_character = _cg_engine_mod.get_character
_cg_pkg.registry = sys.modules["app.services.character_generation.registry"]
_cg_pkg.store = sys.modules["app.services.character_generation.store"]

_load_pkg(
    "app.services.appearance",
    AP,
    [
        ("version", "version.py"),
        ("models", "models.py"),
        ("presets", "presets.py"),
        ("outfits", "outfits.py"),
        ("hairstyle", "hairstyle.py"),
        ("accessories", "accessories.py"),
        ("store", "store.py"),
        ("consistency", "consistency.py"),
        ("appearance_manager", "appearance_manager.py"),
        ("engine", "engine.py"),
    ],
)

cg_engine = sys.modules["app.services.character_generation.engine"]
cg_store = sys.modules["app.services.character_generation.store"]
cg_registry = sys.modules["app.services.character_generation.registry"]
cg_paddle = sys.modules["app.services.character_generation.paddle_status"]

version = sys.modules["app.services.appearance.version"]
models = sys.modules["app.services.appearance.models"]
store = sys.modules["app.services.appearance.store"]
engine = sys.modules["app.services.appearance.engine"]
presets = sys.modules["app.services.appearance.presets"]


def setup_function():
    store.clear()
    cg_store.clear()
    cg_registry.clear()


def test_version():
    assert version.ENGINE_VERSION == "1.0.0"
    assert version.PHASE == 5
    assert version.SPRINT == 3


def test_style_preset_loading():
    listed = presets.list_presets()
    assert len(listed) >= 9
    ids = {p.preset_id for p in listed}
    for expected in (
        "cinematic",
        "realistic",
        "hyper_realistic",
        "luxury",
        "documentary",
        "commercial",
        "music_video",
        "action",
        "fashion",
    ):
        assert expected in ids
    cin = presets.get_preset("Cinematic")
    assert cin is not None
    assert cin.preset_id == "cinematic"
    payload = presets.preset_payload("music_video")
    assert payload["preset"]["name"] == "Music Video"


def test_appearance_persistence():
    char = cg_engine.create_character(
        name="Style Lead",
        registry_slot="Character_A",
        gender="female",
        age=29,
        hairstyle="long_wavy",
        eye_color="amber",
        skin="olive",
    )
    cid = char.character.character_id
    styled = engine.apply_style(
        cid,
        style_preset="cinematic",
        hair_color="dark_brown",
        height="tall",
    )
    assert styled["style_preset_id"] == "cinematic"
    profile = styled["profile"]
    for field in models.APPEARANCE_PROFILE_FIELDS:
        assert field in profile
    assert profile["hairstyle"] == "long_wavy"
    assert profile["eye_color"] == "amber"
    assert profile["skin_tone"] == "olive"
    assert profile["hair_color"] == "dark_brown"

    again = engine.get_style(cid)
    assert again is not None
    assert again["profile"]["hairstyle"] == "long_wavy"
    assert again["profile"]["hair_color"] == "dark_brown"
    assert again["facial_fingerprint"] == styled["facial_fingerprint"]


def test_outfit_switching_preserves_identity():
    char = cg_engine.create_character(
        name="Outfit Switch",
        registry_slot="Character_B",
        hairstyle="short_textured",
        eye_color="green",
    )
    cid = char.character.character_id
    engine.apply_style(cid, style_preset="realistic")
    before = engine.get_style(cid)
    facial = before["facial_fingerprint"]
    hair = before["profile"]["hairstyle"]
    eyes = before["profile"]["eye_color"]

    formal = engine.apply_outfit(cid, category="formal")
    assert formal["identity_preserved"] is True
    assert formal["profile"]["hairstyle"] == hair
    assert formal["profile"]["eye_color"] == eyes
    assert formal["facial_fingerprint"] == facial
    assert formal["profile"]["clothing_style"] == "formal_evening"
    assert formal["active_outfit"]["category"] == "formal"

    sports = engine.apply_outfit(cid, category="sports")
    assert sports["identity_preserved"] is True
    assert sports["facial_fingerprint"] == facial
    assert sports["profile"]["clothing_style"] == "athletic_wear"
    assert sports["profile"]["hairstyle"] == hair

    outfits = engine.get_outfits(cid)
    assert outfits is not None
    assert outfits["count"] >= 6
    cats = {o["category"] for o in outfits["outfits"]}
    assert "casual" in cats and "luxury" in cats and "business" in cats


def test_consistency_validation():
    char = cg_engine.create_character(name="Consistent", registry_slot="Character_C")
    cid = char.character.character_id
    engine.apply_style(cid, style_preset="commercial")
    report = engine.detect_drift(cid)
    assert report["consistent"] is True
    assert report["drift_detected"] is False
    assert report["appearance_score"] >= 90
    assert report["face_preserved"] is True
    assert report["body_preserved"] is True
    assert report["hair_preserved"] is True
    assert report["clothing_match"] is True


def test_appearance_drift_detection():
    char = cg_engine.create_character(name="Drift Style", registry_slot="Character_A")
    cid = char.character.character_id
    engine.apply_style(cid, style_preset="fashion")
    drifted = engine.detect_drift(
        cid,
        candidate_overrides={
            "eye_color": "violet",
            "hairstyle": "buzz_cut",
            "clothing_style": "wrong_outfit",
            "skin_tone": "wrong_tone",
        },
    )
    assert drifted["drift_detected"] is True
    assert drifted["appearance_score"] < 90
    assert drifted["face_preserved"] is False or drifted["hair_preserved"] is False
    traits = {f["trait"] for f in drifted["drift_flags"]}
    assert "eye_color" in traits or "hairstyle" in traits


def test_paddle_still_works():
    status = cg_paddle.paddle_status()
    assert status["secrets_exposed"] is False
    assert "env_presence" in status
    assert all(isinstance(v, bool) for v in status["env_presence"].values())
