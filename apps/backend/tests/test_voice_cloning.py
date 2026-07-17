"""Phase 4 Sprint 3 — Voice Cloning & Character Voice Engine tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VC = ROOT / "app" / "services" / "voice_cloning"


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
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    pkg = type(sys)(pkg_name)
    pkg.__path__ = [str(pkg_path)]
    sys.modules[pkg_name] = pkg
    for mod_name, file_name in modules:
        _load(f"{pkg_name}.{mod_name}", pkg_path / file_name)


_load_pkg(
    "app.services.voice_cloning",
    VC,
    [
        ("version", "version.py"),
        ("models", "models.py"),
        ("validation", "validation.py"),
        ("fingerprint", "fingerprint.py"),
        ("quality", "quality.py"),
        ("security", "security.py"),
        ("observability", "observability.py"),
        ("store", "store.py"),
        ("queue", "queue.py"),
        ("cache", "cache.py"),
        ("character_bridge", "character_bridge.py"),
        ("engine", "engine.py"),
    ],
)

version = sys.modules["app.services.voice_cloning.version"]
validation = sys.modules["app.services.voice_cloning.validation"]
fingerprint = sys.modules["app.services.voice_cloning.fingerprint"]
quality = sys.modules["app.services.voice_cloning.quality"]
security = sys.modules["app.services.voice_cloning.security"]
store = sys.modules["app.services.voice_cloning.store"]
queue_mod = sys.modules["app.services.voice_cloning.queue"]
character_bridge = sys.modules["app.services.voice_cloning.character_bridge"]
engine = sys.modules["app.services.voice_cloning.engine"]


def setup_function():
    store.clear()
    queue_mod.clone_queue.clear()
    security.clear_audit()


def test_version():
    assert version.ENGINE_VERSION == "1.0.0"
    assert "Voice Cloning" in version.ENGINE_NAME
    assert version.SPRINT == 3


def test_validation_rejects_bad_audio():
    bad = validation.validate_clone_reference(
        "/media/refs/bad.txt",
        duration_sec=0.2,
        sample_rate=8000,
        file_type=".txt",
        quality_hint=0.1,
    )
    assert not bad.ok
    assert any("file type" in e.lower() or "short" in e.lower() or "sample" in e.lower() or "quality" in e.lower() for e in bad.errors)


def test_validation_accepts_good_wav():
    good = validation.validate_clone_reference(
        "/media/refs/speaker_a.wav",
        duration_sec=5.0,
        sample_rate=24000,
        file_type=".wav",
        quality_hint=0.8,
    )
    assert good.ok
    assert good.checksum


def test_duplicate_detection():
    first = validation.validate_clone_reference(
        "/media/refs/dup.wav",
        duration_sec=4.0,
        sample_rate=24000,
        file_type=".wav",
        quality_hint=0.7,
    )
    assert first.ok
    second = validation.validate_clone_reference(
        "/media/refs/dup.wav",
        duration_sec=4.0,
        sample_rate=24000,
        file_type=".wav",
        quality_hint=0.7,
        known_checksums={first.checksum},
    )
    assert not second.ok
    assert any("duplicate" in e.lower() for e in second.errors)


def test_fingerprint_and_quality():
    fp = fingerprint.build_fingerprint(
        reference_url="/media/refs/a.wav",
        checksum="abc",
        sample_rate=24000,
        duration_sec=5.0,
    )
    assert fp.fingerprint_id.startswith("vfp_")
    assert fingerprint.verify_speaker(fp)
    q = quality.score_clone_quality(
        fingerprint=fp,
        reference_quality=0.8,
        speaker_verified=True,
        locked=True,
    )
    assert q.overall >= 0.7
    assert q.grade in ("A", "B", "C", "D")
    assert q.speaker_verified


def test_security_ownership_and_signature():
    ctx = security.build_auth_context(owner_id="user_1", backend_secret_ok=True)
    security.assert_ownership("user_1", ctx)
    try:
        security.assert_ownership("user_2", ctx)
        raised = False
    except PermissionError:
        raised = True
    assert raised

    secret = "test-secret-key"
    sig = security.sign_payload("hello", secret)
    assert security.verify_signature("hello", sig, secret)
    assert not security.verify_signature("hello", "t=1,v1=bad", secret)
    entry = security.audit_log("test", clone_id="c1", owner_id="user_1")
    assert entry["provider_secret_exposed"] is False


def test_clone_and_store():
    setup_function()
    job = engine.clone_voice(
        "/media/refs/lead.wav",
        owner_id="owner_a",
        character_id="Character_A_test01",
        language="en",
        gender="female",
        accent="neutral",
        duration_sec=6.0,
        sample_rate=24000,
        file_type=".wav",
        quality_hint=0.85,
        lock_voice=True,
        skip_duplicate_check=True,
    )
    assert job.clone_id.startswith("voiceclone_")
    assert job.state == "completed"
    assert job.production_ready
    assert job.voice_locked
    assert job.fingerprint is not None
    assert job.quality.speaker_verified
    assert job.preview_url
    assert "provider_secret_exposed" in job.metadata
    assert job.metadata["provider_secret_exposed"] is False
    stored = engine.get_clone(job.clone_id)
    assert stored is not None
    char = store.get_character("Character_A_test01")
    assert char is not None
    assert char.clone_id == job.clone_id
    assert char.voice_locked


def test_queue_retry_cancel():
    setup_function()
    job = engine.clone_voice(
        "/media/refs/queue.wav",
        character_id="Character_Q",
        duration_sec=5.0,
        sample_rate=24000,
        file_type=".wav",
        quality_hint=0.8,
        enqueue=True,
        auto_process=False,
        skip_duplicate_check=True,
    )
    assert job.state == "queued"
    processed = engine.process_clone_job(job.clone_id)
    assert processed and processed.state == "completed"
    # Force fail then retry
    queue_mod.clone_queue.update_state(job.clone_id, "failed", error="boom")
    retried = queue_mod.clone_queue.retry(job.clone_id)
    assert retried and retried.state == "retrying"
    assert retried.retry_count >= 1
    again = engine.process_clone_job(job.clone_id)
    assert again and again.state == "completed"

    job2 = engine.clone_voice(
        "/media/refs/cancel.wav",
        duration_sec=5.0,
        sample_rate=24000,
        file_type=".wav",
        quality_hint=0.8,
        enqueue=True,
        auto_process=False,
        skip_duplicate_check=True,
    )
    cancelled = queue_mod.clone_queue.cancel(job2.clone_id)
    assert cancelled and cancelled.state == "cancelled"


def test_train_and_versioning():
    setup_function()
    job = engine.clone_voice(
        "/media/refs/train_base.wav",
        character_id="Character_T",
        duration_sec=5.0,
        sample_rate=24000,
        file_type=".wav",
        quality_hint=0.8,
        skip_duplicate_check=True,
    )
    v1 = job.voice_version
    trained = engine.retrain_clone(
        job.clone_id,
        reference_url="/media/refs/train_v2.wav",
        auto_process=True,
    )
    assert trained.voice_version == v1 + 1
    assert len(trained.training_history) >= 1


def test_character_integration_restore():
    setup_function()
    mem = {
        "character_id": "Character_A_mem",
        "gender": "male",
        "age": "adult",
        "language": "ur",
        "accent": "lahori",
        "speaking_style": "broadcast",
        "emotion_profile": "confident",
    }
    profile = character_bridge.profile_from_character_memory(mem)
    assert profile.default_voice.startswith("rtas_ur_male")
    assert profile.language == "ur"
    assert profile.age_group == "adult"

    job = engine.clone_voice(
        "/media/refs/char_mem.wav",
        character_id="Character_A_mem",
        language="ur",
        gender="male",
        duration_sec=5.0,
        sample_rate=24000,
        file_type=".wav",
        quality_hint=0.9,
        lock_voice=True,
        skip_duplicate_check=True,
    )
    restored = character_bridge.restore_voice_for_generation(
        [{"character_id": "Character_A_mem", "gender": "male"}]
    )
    assert restored is not None
    assert restored.clone_id == job.clone_id
    kwargs = restored.restore_voice_kwargs()
    assert kwargs["language"] == "ur"
    assert kwargs["voice_locked"] is True

    enriched = character_bridge.enrich_character_memory_dicts(
        [{"character_id": "Character_A_mem", "gender": "male"}]
    )
    assert enriched[0]["clone_id"] == job.clone_id
    assert "voice" in enriched[0] or enriched[0].get("default_voice")


def test_voice_switch_and_lock():
    setup_function()
    a = engine.clone_voice(
        "/media/refs/switch_a.wav",
        character_id="Character_S",
        duration_sec=5.0,
        sample_rate=24000,
        file_type=".wav",
        quality_hint=0.8,
        lock_voice=False,
        skip_duplicate_check=True,
    )
    b = engine.clone_voice(
        "/media/refs/switch_b.wav",
        duration_sec=5.0,
        sample_rate=24000,
        file_type=".wav",
        quality_hint=0.8,
        skip_duplicate_check=True,
    )
    switched = engine.switch_character_voice("Character_S", b.clone_id, lock=True)
    assert switched.clone_id == b.clone_id
    assert switched.voice_locked
    # Locked character rejects different clone
    try:
        engine.switch_character_voice("Character_S", a.clone_id, lock=True)
        locked_ok = False
    except PermissionError:
        locked_ok = True
    assert locked_ok


def run_all():
    tests = [
        test_version,
        test_validation_rejects_bad_audio,
        test_validation_accepts_good_wav,
        test_duplicate_detection,
        test_fingerprint_and_quality,
        test_security_ownership_and_signature,
        test_clone_and_store,
        test_queue_retry_cancel,
        test_train_and_versioning,
        test_character_integration_restore,
        test_voice_switch_and_lock,
    ]
    for fn in tests:
        setup_function()
        fn()
    print("OK voice_cloning")


if __name__ == "__main__":
    run_all()
