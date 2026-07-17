"""Multi-Language Dubbing & Localization Engine."""

from __future__ import annotations

import hashlib
from typing import Any

from app.services.localization import store
from app.services.localization.cache import cache_set
from app.services.localization.languages import get_language, list_languages
from app.services.localization.models import (
    AudioTrack,
    JobKind,
    LocalizationJob,
    LocalizationObservability,
    TranslationSegment,
)
from app.services.localization.observability import elapsed_ms, log_loc_event, start_timer
from app.services.localization.queue import localization_queue
from app.services.localization.speakers import detect_speakers
from app.services.localization.subtitles import build_subtitle_cues
from app.services.localization.translation import split_segments, translate_text
from app.services.localization.validation import validate_localization_request
from app.services.localization.version import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    PROVIDER_SIMULATION,
)


def _job_id(kind: str, src: str, tgt: str, text: str) -> str:
    digest = hashlib.sha1(
        f"{kind}|{src}|{tgt}|{text[:200]}|{ENGINE_VERSION}".encode()
    ).hexdigest()
    return f"locjob_{digest[:10]}"


def localize(
    text: str,
    *,
    kind: JobKind = "localize",
    source_language: str = "en",
    target_language: str = "ur",
    duration_sec: float | None = None,
    accent_profile: str | None = None,
    context: str | None = None,
    provider: str = "simulation",
    enqueue: bool = True,
    auto_process: bool = True,
    character_memory: list[dict[str, Any]] | None = None,
    voice_summary: dict[str, Any] | None = None,
    clone_id: str | None = None,
    parent_voice_job_id: str | None = None,
    parent_video_job_id: str | None = None,
    parent_generation_id: str | None = None,
) -> LocalizationJob:
    validation = validate_localization_request(
        text=text,
        source_language=source_language,
        target_language=target_language,
        duration_sec=duration_sec,
    )
    if not validation.ok:
        raise ValueError("; ".join(validation.errors))

    t0 = start_timer()
    src, tgt = validation.source_language, validation.target_language
    job_id = _job_id(kind, src, tgt, validation.text)
    speakers = detect_speakers(
        validation.text,
        character_memory=character_memory,
        voice_summary=voice_summary,
        clone_id=clone_id,
    )
    lang = get_language(tgt)
    accent = accent_profile or lang.accent_default

    timed = split_segments(validation.text, duration_sec=validation.duration_sec)
    segments: list[TranslationSegment] = []
    translated_parts: list[str] = []
    for i, (part, start, end) in enumerate(timed):
        tr = translate_text(
            part,
            source_language=src,
            target_language=tgt,
            context=context or f"segment_{i}",
        )
        spk = speakers[i % len(speakers)].speaker_id if speakers else None
        segments.append(
            TranslationSegment(
                segment_id=f"seg_{job_id}_{i}",
                source_text=part,
                translated_text=tr["translated_text"],
                source_language=src,
                target_language=tgt,
                start_sec=start,
                end_sec=end,
                speaker_id=spk,
                from_memory=bool(tr["from_memory"]),
            )
        )
        translated_parts.append(tr["translated_text"])

    full_translation = " ".join(translated_parts)
    processing_ms = elapsed_ms(t0)
    events = [
        log_loc_event(
            "localization_start",
            translation_job_id=job_id,
            source_language=src,
            target_language=tgt,
            speaker_count=len(speakers),
        )
    ]

    job = LocalizationJob(
        job_id=job_id,
        engine=ENGINE_NAME,
        version=ENGINE_VERSION,
        state="queued",
        kind=kind,
        source_language=src,
        target_language=tgt,
        source_text=validation.text,
        translated_text=full_translation,
        segments=segments,
        speakers=speakers,
        subtitles=[],
        captions=[],
        audio_tracks=[],
        observability=LocalizationObservability(
            translation_job_id=job_id,
            source_language=src,
            target_language=tgt,
            speaker_count=len(speakers),
            processing_time_ms=processing_ms,
            queue_time_ms=0.0,
            provider=PROVIDER_SIMULATION if provider == "simulation" else provider,
            log_events=events,
        ),
        accent_profile=accent,
        voice_preserved=True,
        subtitle_url=f"/media/localization/{job_id}/subs.vtt",
        caption_url=f"/media/localization/{job_id}/caps.vtt",
        dubbed_audio_url=f"/media/localization/{job_id}/dub_{tgt}.wav",
        provider=provider,
        parent_voice_job_id=parent_voice_job_id or (voice_summary or {}).get("job_id"),
        parent_clone_id=clone_id,
        parent_video_job_id=parent_video_job_id,
        parent_generation_id=parent_generation_id,
        character_memory=list(character_memory or []),
        metadata={
            "warnings": validation.warnings,
            "engine_label": ENGINE_LABEL,
            "provider_secret_exposed": False,
            "rtl": lang.rtl,
            "locale": lang.default_locale,
        },
    )

    store.put_job(job)

    if enqueue:
        localization_queue.enqueue(job)
        job.observability.queue_time_ms = round(
            localization_queue.queue_wait_ms(job_id), 3
        )
        store.put_job(job)

    if auto_process:
        job = process_localization_job(job_id) or job

    events.append(
        log_loc_event(
            "localization_complete",
            translation_job_id=job_id,
            source_language=src,
            target_language=tgt,
            speaker_count=len(speakers),
            processing_time_ms=job.observability.processing_time_ms,
            queue_time_ms=job.observability.queue_time_ms,
            retry_count=job.retry_count,
            state=job.state,
        )
    )
    job.observability.log_events = events
    store.put_job(job)
    cache_set(f"loc:{job_id}", job.summary())
    return job


def process_localization_job(job_id: str) -> LocalizationJob | None:
    job = store.get_job(job_id) or localization_queue.get(job_id)
    if not job:
        return None

    t0 = start_timer()
    localization_queue.update_state(job_id, "preparing")
    job.state = "preparing"
    store.put_job(job)

    localization_queue.update_state(job_id, "translating")
    job.state = "translating"
    store.put_job(job)

    if job.kind in ("dub", "localize"):
        localization_queue.update_state(job_id, "voice_generation")
        job.state = "voice_generation"
        job.audio_tracks = [
            AudioTrack(
                track_id=f"trk_{job.job_id}_{job.target_language}",
                language=job.target_language,
                kind="dialogue",
                asset_url=job.dubbed_audio_url,
                duration_sec=job.segments[-1].end_sec if job.segments else 0.0,
                speaker_id=job.speakers[0].speaker_id if job.speakers else None,
            ),
            AudioTrack(
                track_id=f"trk_{job.job_id}_original",
                language=job.source_language,
                kind="original",
                asset_url=f"/media/localization/{job.job_id}/original.wav",
                duration_sec=job.segments[-1].end_sec if job.segments else 0.0,
            ),
        ]
        store.put_job(job)

        localization_queue.update_state(job_id, "lip_sync")
        job.state = "lip_sync"
        job.lip_sync_metadata = {
            "cues": [
                {
                    "segment_id": s.segment_id,
                    "start_sec": s.start_sec,
                    "end_sec": s.end_sec,
                    "speaker_id": s.speaker_id,
                    "viseme_hint": "auto",
                }
                for s in job.segments
            ],
            "synced_to_timeline": True,
            "voice_identity_preserved": job.voice_preserved,
        }
        store.put_job(job)

    localization_queue.update_state(job_id, "subtitle_generation")
    job.state = "subtitle_generation"
    job.subtitles = build_subtitle_cues(
        job.segments, language=job.target_language, job_id=job.job_id
    )
    job.captions = build_subtitle_cues(
        job.segments,
        language=job.target_language,
        job_id=job.job_id,
        as_captions=True,
    )
    store.put_job(job)

    job.production_ready = bool(job.translated_text) and (
        job.kind == "translate" or (bool(job.audio_tracks) and bool(job.subtitles))
    )
    job.observability.processing_time_ms = elapsed_ms(t0)
    localization_queue.update_state(job_id, "completed")
    job.state = "completed"
    job.queue_position = None
    store.put_job(job)

    log_loc_event(
        "localization_processed",
        translation_job_id=job_id,
        source_language=job.source_language,
        target_language=job.target_language,
        speaker_count=len(job.speakers),
        processing_time_ms=job.observability.processing_time_ms,
        queue_time_ms=job.observability.queue_time_ms,
        retry_count=job.retry_count,
        state=job.state,
    )
    return job


def translate(text: str, **kwargs: Any) -> LocalizationJob:
    kwargs["kind"] = "translate"
    return localize(text, **kwargs)


def dub(text: str, **kwargs: Any) -> LocalizationJob:
    kwargs["kind"] = "dub"
    return localize(text, **kwargs)


def localize_dict(**kwargs: Any) -> dict[str, Any]:
    job = localize(**kwargs)
    return {
        "job": job.to_dict(),
        "summary": job.summary(),
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
    }


def translate_dict(**kwargs: Any) -> dict[str, Any]:
    kwargs["kind"] = "translate"
    return localize_dict(**kwargs)


def dub_dict(**kwargs: Any) -> dict[str, Any]:
    kwargs["kind"] = "dub"
    return localize_dict(**kwargs)


def get_job(job_id: str) -> LocalizationJob | None:
    return store.get_job(job_id) or localization_queue.get(job_id)


def languages_payload() -> dict[str, Any]:
    return {"languages": list_languages(), "count": len(list_languages())}
