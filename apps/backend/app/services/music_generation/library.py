"""Music library indexing helpers."""

from __future__ import annotations

import hashlib
from typing import Any

from app.services.music_generation import store
from app.services.music_generation.cache import cache_get, cache_set
from app.services.music_generation.genres import list_genres
from app.services.music_generation.instruments import list_instruments
from app.services.music_generation.models import MusicJob


def library_id_for(job: MusicJob) -> str:
    digest = hashlib.sha1(
        f"{job.genre}|{job.role}|{job.controls.bpm}|{job.controls.key}|{job.job_id}".encode()
    ).hexdigest()[:12]
    return f"mlib_{digest}"


def index_job(job: MusicJob) -> dict[str, Any]:
    lid = library_id_for(job)
    entry = {
        "library_id": lid,
        "job_id": job.job_id,
        "title": job.title,
        "genre": job.genre,
        "role": job.role,
        "bpm": job.controls.bpm,
        "key": job.controls.key,
        "mood": job.controls.mood,
        "duration_sec": job.controls.duration_sec,
        "instruments": list(job.controls.instruments),
        "loop": job.controls.loop,
        "asset_url": job.asset_url,
        "preview_url": job.preview_url,
        "music_version": job.music_version,
        "stems": list(job.controls.stems),
        "stem_urls": dict(job.stem_urls),
    }
    store.put_library_entry(entry)
    job.library_id = lid
    cache_set(f"lib:{lid}", entry)
    cache_invalidate_list()
    return entry


def cache_invalidate_list() -> None:
    from app.services.music_generation.cache import cache_invalidate

    cache_invalidate("library_list:")


def library_payload(
    *,
    genre: str | None = None,
    role: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    cache_key = f"library_list:{genre or '*'}:{role or '*'}:{limit}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    items = store.list_library(genre=genre, role=role, limit=limit)
    payload = {
        "items": items,
        "count": len(items),
        "genres": list_genres(),
        "instruments": list_instruments(),
    }
    cache_set(cache_key, payload, ttl=60.0)
    return payload
