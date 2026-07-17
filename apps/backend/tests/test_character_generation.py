"""Phase 5 Sprint 1 — AI Avatar & Character Generation Engine tests."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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

version = sys.modules["app.services.character_generation.version"]
templates = sys.modules["app.services.character_generation.templates"]
paddle_status = sys.modules["app.services.character_generation.paddle_status"]
registry = sys.modules["app.services.character_generation.registry"]
store = sys.modules["app.services.character_generation.store"]
engine = sys.modules["app.services.character_generation.engine"]
validation = sys.modules["app.services.character_generation.validation"]


def setup_function():
    store.clear()
    registry.clear()


def test_version():
    assert version.ENGINE_VERSION == "1.0.0"
    assert version.PHASE == 5
    assert version.SPRINT == 1
    assert "Avatar" in version.ENGINE_NAME or "Character" in version.ENGINE_NAME


def test_templates():
    tmpls = templates.list_templates()
    assert len(tmpls) >= 3
    assert templates.get_template("cinematic_lead").template_id == "cinematic_lead"


def test_create_character_identity_and_dna():
    job = engine.create_character(
        name="Aria Lead",
        prompt="Cinematic heroine under rain",
        template_id="cinematic_lead",
        registry_slot="Character_A",
        gender="female",
        age=27,
        eye_color="amber",
        accessories=["necklace"],
    )
    assert job.state == "completed"
    assert job.character.production_ready
    ident = job.character.identity
    assert ident.unique_id.startswith("cuid_")
    assert ident.version == "1.0.0"
    assert ident.gender == "female"
    assert ident.age == 27
    assert ident.ethnicity
    assert ident.body_type
    assert ident.hairstyle
    assert ident.beard is not None
    assert ident.skin
    assert ident.eye_color == "amber"
    assert ident.clothing
    assert "necklace" in ident.accessories

    dna = job.character.dna.to_character_dna_json()
    assert dna["format"] == "rtas-character-dna-v1"
    assert dna["fingerprint"]
    assert dna["locked"] is True
    assert job.character.dna_url.endswith("character_dna.json")
    assert job.character.registry_slot == "Character_A"


def test_registry_abc():
    engine.create_character(name="A", registry_slot="Character_A")
    engine.create_character(name="B", registry_slot="Character_B")
    engine.create_character(name="C", registry_slot="Character_C")
    payload = registry.registry_payload()
    assert payload["count"] == 3
    assert payload["slots"]["Character_A"] is not None
    assert payload["slots"]["Character_B"] is not None
    assert payload["slots"]["Character_C"] is not None
    listed = engine.list_characters()
    assert listed["count"] == 3
    assert listed["slots_filled"] == 3


def test_get_avatar_by_id_and_slot():
    job = engine.create_character(name="Recall Me", registry_slot="B")
    cid = job.character.character_id
    by_char = engine.get_avatar_payload(cid)
    assert by_char and by_char["character_id"] == cid
    by_job = engine.get_avatar_payload(job.job_id)
    assert by_job and by_job["job_id"] == job.job_id
    by_slot = engine.get_avatar_payload("Character_B")
    assert by_slot and by_slot["character_id"] == cid


def test_validation():
    bad = validation.validate_create_request(registry_slot="Character_Z", age=200)
    assert not bad.ok
    good = validation.validate_create_request(registry_slot="A", age=30)
    assert good.ok
    assert good.registry_slot == "Character_A"


def test_paddle_status_no_secrets():
    # Ensure verification never returns secret values
    os.environ.pop("PADDLE_WEBHOOK_SECRET", None)
    status = paddle_status.paddle_status()
    assert "secrets_exposed" in status
    assert status["secrets_exposed"] is False
    assert "env_presence" in status
    # Presence map values are booleans only
    assert all(isinstance(v, bool) for v in status["env_presence"].values())
    blob = str(status)
    assert "whsec_" not in blob
    assert "pdl_" not in blob

    # With defer flag, configured can be true without keys
    os.environ["RTAS_DEFER_PADDLE"] = "1"
    os.environ["NEXT_PUBLIC_PAYMENT_PROVIDER"] = "paddle"
    deferred = paddle_status.paddle_status()
    assert deferred["deferred"] is True
    assert deferred["configured"] is True
    assert deferred["message"] in (
        "paddle-deferred-until-keys",
        "paddle-ready",
    )
    os.environ.pop("RTAS_DEFER_PADDLE", None)


def test_dna_persists_across_lookup():
    job = engine.create_character(name="Persistent DNA", registry_slot="Character_A")
    fp = job.character.dna.fingerprint
    again = engine.get_character(job.character.character_id)
    assert again is not None
    assert again.dna.fingerprint == fp
    assert again.dna.version == 1
