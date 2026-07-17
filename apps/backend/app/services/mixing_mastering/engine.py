"""Mixing & Mastering Engine — automatic production-ready audio master."""

from __future__ import annotations

import hashlib
from typing import Any

from app.services.mixing_mastering import store
from app.services.mixing_mastering.bridge import adapt_from_pipeline
from app.services.mixing_mastering.cache import cache_set
from app.services.mixing_mastering.mastering import build_master_profile, describe_master_chain
from app.services.mixing_mastering.mixing import build_mix_profile, describe_mix_chain
from app.services.mixing_mastering.models import (
    JobKind,
    MixMasterJob,
    MixObservability,
)
from app.services.mixing_mastering.observability import elapsed_ms, log_mix_event, start_timer
from app.services.mixing_mastering.quality import parallel_analyze
from app.services.mixing_mastering.queue import mix_queue
from app.services.mixing_mastering.validation import validate_mix_master_request
from app.services.mixing_mastering.version import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    PROVIDER_SIMULATION,
)


def _job_id(kind: str, parents: str) -> str:
    digest = hashlib.sha1(f"{kind}|{parents}|{ENGINE_VERSION}".encode()).hexdigest()
    return f"mixjob_{digest[:10]}"


def _master_id(mix_id: str) -> str:
    digest = hashlib.sha1(f"master|{mix_id}|{ENGINE_VERSION}".encode()).hexdigest()
    return f"masterjob_{digest[:10]}"


def run_mix_master(
    *,
    kind: JobKind = "mix_master",
    target_lufs: float | None = None,
    true_peak_ceiling: float | None = None,
    export_format: str | None = None,
    sample_rate: int | None = None,
    bit_depth: int | None = None,
    dialogue_priority: bool = True,
    music_ducking_db: float | None = None,
    sfx_balance: float | None = None,
    ambient_level: float | None = None,
    stereo_width: float | None = None,
    noise_reduction: bool = True,
    provider: str = "simulation",
    enqueue: bool = True,
    auto_process: bool = True,
    voice_summary: dict[str, Any] | None = None,
    music_summary: dict[str, Any] | None = None,
    sfx_summary: dict[str, Any] | None = None,
    audio_engine_summary: dict[str, Any] | None = None,
    video_engine: dict[str, Any] | None = None,
    parent_generation_id: str | None = None,
) -> MixMasterJob:
    validation = validate_mix_master_request(
        target_lufs=target_lufs,
        true_peak_ceiling=true_peak_ceiling,
        export_format=export_format,
        sample_rate=sample_rate,
        bit_depth=bit_depth,
        music_ducking_db=music_ducking_db,
    )
    if not validation.ok:
        raise ValueError("; ".join(validation.errors))

    adapted = adapt_from_pipeline(
        voice_summary=voice_summary,
        music_summary=music_summary,
        sfx_summary=sfx_summary,
        audio_engine_summary=audio_engine_summary,
        video_engine=video_engine,
    )
    parents = "|".join(
        str(adapted.get(k) or "")
        for k in (
            "parent_voice_job_id",
            "parent_music_job_id",
            "parent_sfx_job_id",
            "parent_audio_job_id",
            "parent_video_job_id",
        )
    )
    t0 = start_timer()
    job_id = _job_id(kind, parents)
    master_id = _master_id(job_id) if kind in ("master", "mix_master") else None

    mix_profile = build_mix_profile(
        dialogue_priority=dialogue_priority,
        music_ducking_db=music_ducking_db,
        sfx_balance=sfx_balance,
        ambient_level=ambient_level,
        voice_summary=voice_summary,
        music_summary=music_summary,
        sfx_summary=sfx_summary,
    )
    master_profile = build_master_profile(
        target_lufs=validation.target_lufs,
        true_peak_ceiling=validation.true_peak_ceiling,
        stereo_width=stereo_width,
        noise_reduction=noise_reduction,
    )

    # Initial pre-mix analysis
    analysis = parallel_analyze(
        job_id,
        target_lufs=validation.target_lufs,
        true_peak_ceiling=validation.true_peak_ceiling,
        stereo_width=master_profile.stereo_width,
        normalized=False,
    )
    processing_ms = elapsed_ms(t0)
    events = [
        log_mix_event(
            "mix_master_start",
            mix_job_id=job_id,
            master_job_id=master_id,
        )
    ]

    job = MixMasterJob(
        job_id=job_id,
        engine=ENGINE_NAME,
        version=ENGINE_VERSION,
        state="queued",
        kind=kind,
        mix_job_id=job_id,
        master_job_id=master_id,
        mix_profile=mix_profile,
        master_profile=master_profile,
        loudness=analysis["loudness"],
        frequency=analysis["frequency"],
        quality=analysis["quality"],
        observability=MixObservability(
            mix_job_id=job_id,
            master_job_id=master_id,
            processing_time_ms=processing_ms,
            queue_time_ms=0.0,
            loudness_lufs=analysis["loudness"].integrated_lufs,
            quality_score=analysis["quality"].overall_score,
            provider=PROVIDER_SIMULATION if provider == "simulation" else provider,
            log_events=events,
        ),
        asset_url=f"/media/mix/{job_id}/mix.wav",
        master_url=f"/media/master/{master_id or job_id}/master.{validation.export_format}",
        export_format=validation.export_format,
        export_sample_rate=validation.sample_rate,
        export_bit_depth=validation.bit_depth,
        provider=provider,
        parent_voice_job_id=adapted.get("parent_voice_job_id"),
        parent_music_job_id=adapted.get("parent_music_job_id"),
        parent_sfx_job_id=adapted.get("parent_sfx_job_id"),
        parent_audio_job_id=adapted.get("parent_audio_job_id"),
        parent_video_job_id=adapted.get("parent_video_job_id"),
        parent_generation_id=parent_generation_id,
        metadata={
            "warnings": validation.warnings,
            "engine_label": ENGINE_LABEL,
            "provider_secret_exposed": False,
            "mix_chain": describe_mix_chain(mix_profile),
            "master_chain": describe_master_chain(master_profile),
            "pipeline": adapted,
        },
    )

    store.put_job(job)

    if enqueue:
        mix_queue.enqueue(job)
        job.observability.queue_time_ms = round(mix_queue.queue_wait_ms(job_id), 3)
        store.put_job(job)

    if auto_process:
        job = process_mix_job(job_id) or job

    events.append(
        log_mix_event(
            "mix_master_complete",
            mix_job_id=job_id,
            master_job_id=job.master_job_id,
            processing_time_ms=job.observability.processing_time_ms,
            queue_time_ms=job.observability.queue_time_ms,
            loudness=job.loudness.integrated_lufs,
            quality_score=job.quality.overall_score,
            retry_count=job.retry_count,
            state=job.state,
        )
    )
    job.observability.log_events = events
    store.put_job(job)
    cache_set(f"mix:{job_id}", job.summary())
    if job.master_job_id:
        cache_set(f"master:{job.master_job_id}", job.summary())
    return job


def process_mix_job(job_id: str) -> MixMasterJob | None:
    job = store.get_job(job_id) or mix_queue.get(job_id)
    if not job:
        return None

    t0 = start_timer()
    mix_queue.update_state(job.job_id, "preparing")
    job.state = "preparing"
    store.put_job(job)

    if job.kind in ("mix", "mix_master"):
        mix_queue.update_state(job.job_id, "mixing")
        job.state = "mixing"
        store.put_job(job)

    if job.kind in ("master", "mix_master"):
        mix_queue.update_state(job.job_id, "mastering")
        job.state = "mastering"
        if not job.master_job_id:
            job.master_job_id = _master_id(job.job_id)
        store.put_job(job)

    mix_queue.update_state(job.job_id, "quality_check")
    job.state = "quality_check"
    store.put_job(job)

    # Post-master normalized analysis
    analysis = parallel_analyze(
        job.job_id,
        target_lufs=job.master_profile.target_lufs,
        true_peak_ceiling=job.master_profile.true_peak_ceiling_dbtp,
        stereo_width=job.master_profile.stereo_width,
        normalized=True,
    )
    job.loudness = analysis["loudness"]
    job.frequency = analysis["frequency"]
    job.quality = analysis["quality"]
    job.observability.loudness_lufs = job.loudness.integrated_lufs
    job.observability.quality_score = job.quality.overall_score
    job.observability.processing_time_ms = elapsed_ms(t0)
    job.production_ready = job.quality.production_ready

    mix_queue.update_state(job.job_id, "completed")
    job.state = "completed"
    job.queue_position = None
    store.put_job(job)

    log_mix_event(
        "mix_job_processed",
        mix_job_id=job.job_id,
        master_job_id=job.master_job_id,
        processing_time_ms=job.observability.processing_time_ms,
        queue_time_ms=job.observability.queue_time_ms,
        loudness=job.loudness.integrated_lufs,
        quality_score=job.quality.overall_score,
        retry_count=job.retry_count,
        state=job.state,
    )
    return job


def mix_audio(**kwargs: Any) -> MixMasterJob:
    kwargs["kind"] = "mix"
    return run_mix_master(**kwargs)


def master_audio(**kwargs: Any) -> MixMasterJob:
    kwargs["kind"] = "master"
    return run_mix_master(**kwargs)


def mix_master_dict(**kwargs: Any) -> dict[str, Any]:
    job = run_mix_master(**kwargs)
    return {
        "job": job.to_dict(),
        "summary": job.summary(),
        "quality_report": job.quality.to_dict(),
        "loudness": job.loudness.to_dict(),
        "frequency": job.frequency.to_dict(),
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
    }


def mix_dict(**kwargs: Any) -> dict[str, Any]:
    kwargs["kind"] = "mix"
    return mix_master_dict(**kwargs)


def master_dict(**kwargs: Any) -> dict[str, Any]:
    kwargs["kind"] = "master"
    return mix_master_dict(**kwargs)


def get_job(job_id: str) -> MixMasterJob | None:
    return store.get_job(job_id) or mix_queue.get(job_id)


def get_quality_report(job_id: str) -> dict[str, Any] | None:
    job = get_job(job_id)
    if not job:
        return None
    return {
        "job_id": job.job_id,
        "mix_job_id": job.mix_job_id or job.job_id,
        "master_job_id": job.master_job_id,
        "quality": job.quality.to_dict(),
        "loudness": job.loudness.to_dict(),
        "frequency": job.frequency.to_dict(),
        "production_ready": job.production_ready,
        "export": {
            "format": job.export_format,
            "sample_rate": job.export_sample_rate,
            "bit_depth": job.export_bit_depth,
            "master_url": job.master_url,
        },
    }
