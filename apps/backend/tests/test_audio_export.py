"""Phase 4 Sprint 9 — Audio Export, Delivery & Distribution tests."""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EX = ROOT / "app" / "services" / "audio_export"


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
    "app.services.audio_export",
    EX,
    [
        ("version", "version.py"),
        ("models", "models.py"),
        ("profiles", "profiles.py"),
        ("validation", "validation.py"),
        ("packaging", "packaging.py"),
        ("security", "security.py"),
        ("cache", "cache.py"),
        ("store", "store.py"),
        ("queue", "queue.py"),
        ("observability", "observability.py"),
        ("engine", "engine.py"),
    ],
)

version = sys.modules["app.services.audio_export.version"]
profiles = sys.modules["app.services.audio_export.profiles"]
validation = sys.modules["app.services.audio_export.validation"]
security = sys.modules["app.services.audio_export.security"]
store = sys.modules["app.services.audio_export.store"]
queue_mod = sys.modules["app.services.audio_export.queue"]
engine = sys.modules["app.services.audio_export.engine"]
cache = sys.modules["app.services.audio_export.cache"]


def setup_function():
    store.clear()
    queue_mod.export_queue.clear()
    cache.cache_clear()


def test_version():
    assert version.ENGINE_VERSION == "1.0.0"
    assert "Export" in version.ENGINE_NAME
    assert version.SPRINT == 9


def test_platform_profiles():
    required = {
        "youtube",
        "youtube_shorts",
        "tiktok",
        "instagram_reels",
        "facebook",
        "linkedin",
        "x_twitter",
        "snapchat",
        "website",
        "commercial_broadcast",
    }
    ids = {p.profile_id for p in profiles.list_profiles()}
    assert required <= ids
    yt = profiles.get_profile("youtube")
    assert yt is not None
    assert yt.resolution == "1920x1080"
    assert yt.audio_loudness_lufs == -14.0
    assert profiles.get_profile("twitter").profile_id == "x_twitter"
    payload = profiles.profiles_payload()
    assert set(payload["audio_formats"]) == {"wav", "mp3", "flac", "aac", "ogg"}
    assert set(payload["video_formats"]) == {"mp4", "mov", "mkv", "webm"}


def test_validation():
    bad = validation.validate_export_request(platform="nope")
    assert not bad.ok
    good = validation.validate_export_request(
        platform="tiktok", quality="high", formats=["mp3", "wav"]
    )
    assert good.ok


def test_create_export_package():
    job = engine.create_export(
        platform="youtube",
        quality="high",
        formats=["wav", "mp3"],
        watermark=True,
        duration_sec=8,
        timeline_summary={"job_id": "tl1", "duration_sec": 8, "track_count": 7},
        localization_summary={
            "job_id": "loc1",
            "subtitle_url": "/subs.vtt",
            "caption_url": "/caps.vtt",
        },
        enqueue=True,
        auto_process=True,
    )
    assert job.state == "completed"
    assert job.production_ready
    assert job.verified
    assert job.signed_url
    assert job.watermark
    kinds = {a.kind for a in job.assets}
    assert {"video", "audio", "subtitle", "caption", "thumbnail", "metadata", "package"} <= kinds
    assert all(a.verified for a in job.assets)
    statuses = [h["status"] for h in job.history]
    for required in (
        "queued",
        "preparing",
        "packaging",
        "exporting",
        "compressing",
        "uploading",
        "completed",
    ):
        assert required in statuses


def test_batch_export():
    jobs = engine.create_batch_exports(
        ["youtube", "tiktok", "instagram_reels"],
        duration_sec=4,
        enqueue=True,
        auto_process=True,
    )
    assert len(jobs) == 3
    assert len({j.batch_id for j in jobs}) == 1
    assert all(j.state == "completed" for j in jobs)


def test_download_and_security():
    job = engine.create_export(platform="website", duration_sec=3)
    dl = engine.download_export(job.job_id)
    assert dl["authorized"] is True
    assert dl["streaming"] is True
    assert dl["download_count"] == 1

    # Invalid token denied
    try:
        engine.download_export(job.job_id, token="badtoken")
        assert False, "expected unauthorized"
    except ValueError as exc:
        assert "invalid_token" in str(exc)

    # Expired ticket
    check = security.validate_download(
        export_job_id=job.job_id,
        token="any",
        expires_at=time.time() - 10,
        package_url=job.package_url or "/x.zip",
    )
    # Invalid token fails first; use a correctly signed but expired ticket
    ticket = security.create_signed_download(
        job.job_id, package_url=job.package_url or "/x.zip", expire_hours=1.0
    )
    check = security.validate_download(
        export_job_id=job.job_id,
        token=ticket.token,
        expires_at=time.time() - 5,
        package_url=job.package_url or "/x.zip",
    )
    # Token was signed with future expiry, so signature won't match past expires_at
    assert check["ok"] is False
    assert check["error"] in ("expired", "invalid_token")

    # Explicit expired check with matching signature payload
    import hmac as _hmac
    import hashlib as _hashlib

    past = time.time() - 30
    pkg = job.package_url or "/x.zip"
    payload = f"{job.job_id}|{past}|{pkg}"
    token = _hmac.new(
        b"rtas-export-sim-signing-key-v1", payload.encode(), _hashlib.sha256
    ).hexdigest()[:32]
    check2 = security.validate_download(
        export_job_id=job.job_id,
        token=token,
        expires_at=past,
        package_url=pkg,
    )
    assert check2["ok"] is False
    assert check2["error"] == "expired"


def test_queue_retry():
    job = engine.create_export(platform="facebook", duration_sec=2)
    assert job.state == "completed"
    retried = queue_mod.export_queue.retry(job.job_id)
    assert retried is not None
    assert retried.state == "retrying"
    assert retried.retry_count >= 1
    processed = engine.process_export_job(job.job_id)
    assert processed is not None
    assert processed.state == "completed"


def test_history_and_get_job():
    job = engine.create_export(
        platform="linkedin",
        duration_sec=2,
        parent_generation_id="gen_export_9",
    )
    hist = engine.history_payload(limit=10, parent_generation_id="gen_export_9")
    assert hist["items"]
    assert any(i.get("export_job_id") == job.job_id for i in hist["items"])
    fetched = engine.get_job(job.job_id)
    assert fetched is not None
    assert fetched.job_id == job.job_id


def test_commercial_broadcast_preset():
    job = engine.create_export(platform="commercial_broadcast", quality="broadcast")
    assert job.profile.resolution == "3840x2160"
    assert job.profile.video_format == "mov"
    assert job.profile.audio_format == "wav"
    assert job.profile.metadata_format == "xml"


def test_resume_export():
    job = engine.create_export(platform="snapchat", duration_sec=2, auto_process=False)
    assert job.state == "queued"
    resumed = engine.resume_export(job.job_id)
    assert resumed.state == "completed"


def test_performance_exports_under_budget():
    t0 = time.perf_counter()
    for i in range(15):
        engine.create_export(
            platform="youtube" if i % 2 == 0 else "tiktok",
            duration_sec=3,
            formats=["mp3"],
        )
    elapsed = time.perf_counter() - t0
    assert elapsed < 5.0


def test_no_provider_secret_leak():
    job = engine.create_export(platform="youtube", duration_sec=2)
    payload = job.to_dict()
    blob = str(payload)
    assert "provider_secret" not in blob.lower() or payload["metadata"]["provider_secret_exposed"] is False
    assert "rtas-export-sim-signing-key" not in blob
