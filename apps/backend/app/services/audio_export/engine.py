"""Audio Export, Delivery & Distribution Engine."""

from __future__ import annotations

import hashlib
import time
from typing import Any

from app.services.audio_export import store
from app.services.audio_export.cache import cache_get, cache_set
from app.services.audio_export.models import (
    ExportAnalytics,
    ExportJob,
    ExportObservability,
    ExportVersion,
)
from app.services.audio_export.observability import elapsed_ms, log_export_event, start_timer
from app.services.audio_export.packaging import build_package_assets, verify_assets
from app.services.audio_export.profiles import get_profile, profiles_payload
from app.services.audio_export.queue import export_queue
from app.services.audio_export.security import create_signed_download, validate_download
from app.services.audio_export.validation import validate_export_request
from app.services.audio_export.version import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    PROVIDER_SIMULATION,
)


def _job_id(*parts: str) -> str:
    digest = hashlib.sha1(
        ("|".join(parts) + f"|{ENGINE_VERSION}").encode()
    ).hexdigest()
    return f"expjob_{digest[:10]}"


def _snapshot(job: ExportJob) -> dict[str, Any]:
    return {
        "state": job.state,
        "platform": job.profile.platform,
        "asset_count": len(job.assets),
        "export_size_bytes": job.observability.export_size_bytes,
        "export_version": job.export_version,
        "verified": job.verified,
    }


def create_export(
    *,
    platform: str = "youtube",
    quality: str = "high",
    formats: list[str] | None = None,
    watermark: bool = False,
    duration_sec: float | None = None,
    expire_hours: float = 24.0,
    batch_id: str | None = None,
    include_subtitles: bool = True,
    include_captions: bool = True,
    include_thumbnail: bool = True,
    provider: str = "simulation",
    enqueue: bool = True,
    auto_process: bool = True,
    timeline_summary: dict[str, Any] | None = None,
    localization_summary: dict[str, Any] | None = None,
    video_summary: dict[str, Any] | None = None,
    mix_summary: dict[str, Any] | None = None,
    character_memory: list[dict[str, Any]] | None = None,
    parent_timeline_job_id: str | None = None,
    parent_video_job_id: str | None = None,
    parent_localization_job_id: str | None = None,
    parent_mix_job_id: str | None = None,
    parent_generation_id: str | None = None,
) -> ExportJob:
    validation = validate_export_request(
        platform=platform,
        quality=quality,
        formats=formats,
        watermark=watermark,
        expire_hours=expire_hours,
    )
    if not validation.ok:
        raise ValueError("; ".join(validation.errors))

    profile = get_profile(validation.platform)
    if profile is None:
        raise ValueError(f"unsupported platform: {validation.platform}")

    t0 = start_timer()
    duration = float(duration_sec) if duration_sec is not None else 0.0
    if duration <= 0:
        duration = float(
            (timeline_summary or {}).get("duration_sec")
            or (video_summary or {}).get("duration_sec")
            or 8.0
        )

    job_id = _job_id(
        validation.platform,
        validation.quality,
        str(parent_generation_id or ""),
        str(parent_timeline_job_id or ""),
        str(duration),
        ",".join(validation.formats),
    )

    # Compression cache hit for identical packaging key
    cache_key = f"pkg:{job_id}"
    cached = cache_get(cache_key)

    assets = build_package_assets(
        job_id,
        profile,
        duration_sec=duration,
        quality=validation.quality,
        watermark=validation.watermark,
        include_subtitles=include_subtitles,
        include_captions=include_captions,
        include_thumbnail=include_thumbnail,
        extra_audio_formats=[f for f in validation.formats if f in ("wav", "mp3", "flac", "aac", "ogg")],
        timeline_summary=timeline_summary,
        localization_summary=localization_summary,
    )
    package_asset = next((a for a in assets if a.kind == "package"), assets[-1])
    export_size = package_asset.size_bytes
    processing_ms = elapsed_ms(t0)

    resolved_formats = list(
        dict.fromkeys(
            [profile.video_format, profile.audio_format]
            + validation.formats
            + [profile.metadata_format]
        )
    )

    job = ExportJob(
        job_id=job_id,
        engine=ENGINE_NAME,
        version=ENGINE_VERSION,
        state="queued",
        profile=profile,
        assets=assets,
        observability=ExportObservability(
            export_job_id=job_id,
            export_format=f"{profile.video_format}+{profile.audio_format}",
            resolution=profile.resolution,
            processing_time_ms=processing_ms,
            queue_time_ms=0.0,
            export_size_bytes=export_size,
            provider=PROVIDER_SIMULATION if provider == "simulation" else provider,
            log_events=[
                log_export_event(
                    "export_create",
                    export_job_id=job_id,
                    platform=profile.platform,
                    format=profile.video_format,
                    resolution=profile.resolution,
                )
            ],
        ),
        analytics=ExportAnalytics(
            export_job_id=job_id,
            platform=profile.platform,
            format=profile.video_format,
            size_bytes=export_size,
            processing_time_ms=processing_ms,
            download_count=0,
            success=False,
            compression_ratio=0.88,
        ),
        package_url=package_asset.url,
        download_url=None,
        signed_url=None,
        watermark=validation.watermark,
        batch_id=batch_id,
        production_ready=False,
        verified=False,
        resume_token=f"resume_{job_id}",
        export_version=1,
        provider=provider,
        parent_timeline_job_id=parent_timeline_job_id
        or (timeline_summary or {}).get("job_id"),
        parent_video_job_id=parent_video_job_id or (video_summary or {}).get("job_id"),
        parent_localization_job_id=parent_localization_job_id
        or (localization_summary or {}).get("job_id"),
        parent_mix_job_id=parent_mix_job_id or (mix_summary or {}).get("job_id"),
        parent_generation_id=parent_generation_id,
        formats=resolved_formats,
        quality=validation.quality,
        metadata={
            "expire_hours": validation.expire_hours,
            "duration_sec": duration,
            "character_count": len(character_memory or []),
            "cached_package": bool(cached),
            "provider_secret_exposed": False,
        },
    )
    job.versions.append(
        ExportVersion(
            version=1,
            label="initial",
            snapshot=_snapshot(job),
            created_at=time.time(),
        )
    )
    job.history.append({"status": "queued", "snapshot": _snapshot(job), "ts": time.time()})

    store.save(job)
    store.append_history(
        {
            "export_job_id": job.job_id,
            "status": job.state,
            "platform": profile.platform,
            "format": profile.video_format,
            "resolution": profile.resolution,
            "export_size_bytes": export_size,
            "parent_generation_id": parent_generation_id,
            "snapshot": _snapshot(job),
        }
    )
    cache_set(cache_key, {"job_id": job_id, "size_bytes": export_size})

    if enqueue:
        export_queue.enqueue(job)
        job.observability.queue_time_ms = round(export_queue.queue_wait_ms(job_id), 3)
        store.save(job)

    if auto_process:
        job = process_export_job(job_id) or job

    return job


def process_export_job(job_id: str) -> ExportJob | None:
    job = store.get(job_id) or export_queue.get(job_id)
    if not job:
        return None

    t0 = start_timer()
    queue_ms = export_queue.queue_wait_ms(job_id)
    job.observability.queue_time_ms = max(job.observability.queue_time_ms, queue_ms)

    try:
        for state in ("preparing", "packaging", "exporting", "compressing", "uploading"):
            export_queue.update_state(job_id, state)  # type: ignore[arg-type]
            job.state = state  # type: ignore[assignment]
            job.history.append({"status": state, "ts": time.time()})
            store.save(job)

        ok, errors = verify_assets(job.assets)
        if not ok:
            raise ValueError("; ".join(errors))

        expire_hours = float(job.metadata.get("expire_hours") or 24.0)
        ticket = create_signed_download(
            job.job_id,
            package_url=job.package_url or f"/media/export/{job.job_id}/package.zip",
            expire_hours=expire_hours,
        )
        job.signed_url = ticket.signed_url
        job.download_url = ticket.signed_url
        job.expires_at = ticket.expires_at
        job.verified = True
        job.production_ready = True
        job.export_version += 1
        job.versions.append(
            ExportVersion(
                version=job.export_version,
                label="packaged",
                snapshot=_snapshot(job),
                created_at=time.time(),
            )
        )
        job.delivery_logs.append(
            {
                "event": "uploaded",
                "url": job.package_url,
                "signed": True,
                "ts": time.time(),
            }
        )
        job.observability.processing_time_ms += elapsed_ms(t0)
        job.analytics.processing_time_ms = job.observability.processing_time_ms
        job.analytics.success = True
        job.analytics.size_bytes = job.observability.export_size_bytes

        export_queue.update_state(job_id, "completed")
        job.state = "completed"
        job.history.append(
            {"status": "completed", "snapshot": _snapshot(job), "ts": time.time()}
        )
        job.observability.log_events.append(
            log_export_event(
                "export_completed",
                export_job_id=job.job_id,
                export_format=job.observability.export_format,
                resolution=job.observability.resolution,
                export_size_bytes=job.observability.export_size_bytes,
                processing_time_ms=job.observability.processing_time_ms,
            )
        )
        store.save(job)
        store.append_history(
            {
                "export_job_id": job.job_id,
                "status": "completed",
                "platform": job.profile.platform,
                "format": job.profile.video_format,
                "resolution": job.profile.resolution,
                "export_size_bytes": job.observability.export_size_bytes,
                "parent_generation_id": job.parent_generation_id,
                "snapshot": _snapshot(job),
            }
        )
        store.append_analytics(job.analytics.to_dict())
        store.append_audit(
            {
                "action": "export_completed",
                "export_job_id": job.job_id,
                "authorized": True,
            }
        )
        cache_set(job.job_id, job.summary())
        return job
    except Exception as exc:  # noqa: BLE001
        export_queue.update_state(job_id, "failed", error=str(exc))
        job.state = "failed"
        job.observability.errors.append(str(exc))
        job.analytics.success = False
        job.history.append({"status": "failed", "error": str(exc), "ts": time.time()})
        store.save(job)
        return job


def create_batch_exports(
    platforms: list[str],
    **kwargs: Any,
) -> list[ExportJob]:
    batch_id = kwargs.pop("batch_id", None) or f"batch_{int(time.time())}"
    kwargs.pop("platform", None)
    jobs: list[ExportJob] = []
    for platform in platforms:
        jobs.append(create_export(platform=platform, batch_id=batch_id, **kwargs))
    return jobs


def package_export(**kwargs: Any) -> ExportJob:
    """Alias for create with packaging focus."""
    return create_export(**kwargs)


def download_export(
    job_id: str,
    *,
    token: str | None = None,
) -> dict[str, Any]:
    job = store.get(job_id) or export_queue.get(job_id)
    if not job:
        raise ValueError(f"export not found: {job_id}")
    if job.state != "completed":
        process_export_job(job_id)
        job = store.get(job_id) or job

    package_url = job.package_url or f"/media/export/{job.job_id}/package.zip"
    expires_at = float(job.expires_at or (time.time() + 86400))

    # Extract token from signed URL if not provided
    resolved_token = token
    if not resolved_token and job.signed_url and "token=" in job.signed_url:
        resolved_token = job.signed_url.split("token=")[1].split("&")[0]

    if not resolved_token:
        ticket = create_signed_download(
            job.job_id,
            package_url=package_url,
            expire_hours=float(job.metadata.get("expire_hours") or 24.0),
        )
        job.signed_url = ticket.signed_url
        job.download_url = ticket.signed_url
        job.expires_at = ticket.expires_at
        resolved_token = ticket.token
        expires_at = ticket.expires_at
        store.save(job)

    check = validate_download(
        export_job_id=job.job_id,
        token=resolved_token or "",
        expires_at=expires_at,
        package_url=package_url,
        download_count=job.observability.download_count,
    )
    if not check["ok"]:
        store.append_audit(
            {
                "action": "download_denied",
                "export_job_id": job.job_id,
                "error": check.get("error"),
                "authorized": False,
            }
        )
        raise ValueError(check.get("error") or "unauthorized")

    job.observability.download_count += 1
    job.analytics.download_count = job.observability.download_count
    job.download_history.append(
        {
            "ts": time.time(),
            "authorized": True,
            "download_count": job.observability.download_count,
        }
    )
    store.save(job)
    store.append_audit(
        {
            "action": "download_granted",
            "export_job_id": job.job_id,
            "authorized": True,
            "download_count": job.observability.download_count,
        }
    )
    return {
        "job_id": job.job_id,
        "signed_url": job.signed_url,
        "download_url": job.download_url,
        "expires_at": job.expires_at,
        "authorized": True,
        "download_count": job.observability.download_count,
        "export_size_bytes": job.observability.export_size_bytes,
        "streaming": True,
        "assets": [a.to_dict() for a in job.assets],
    }


def resume_export(job_id: str) -> ExportJob:
    job = store.get(job_id) or export_queue.get(job_id)
    if not job:
        raise ValueError(f"export not found: {job_id}")
    if job.state == "completed":
        return job
    export_queue.retry(job_id)
    return process_export_job(job_id) or job


def get_job(job_id: str) -> ExportJob | None:
    return store.get(job_id) or export_queue.get(job_id)


def create_export_dict(**kwargs: Any) -> dict[str, Any]:
    return create_export(**kwargs).to_dict()


def package_export_dict(**kwargs: Any) -> dict[str, Any]:
    return package_export(**kwargs).to_dict()


def history_payload(
    *,
    limit: int = 50,
    parent_generation_id: str | None = None,
) -> dict[str, Any]:
    return {
        "items": store.history(limit=limit, parent_generation_id=parent_generation_id),
        "queue": export_queue.status(),
        "analytics": store.analytics(limit=min(20, limit)),
        "engine": ENGINE_LABEL,
    }
