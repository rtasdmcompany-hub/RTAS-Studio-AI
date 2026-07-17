"""SFX / ambient asset library indexing."""

from __future__ import annotations

from typing import Any

from app.services.sfx_ambient import store
from app.services.sfx_ambient.categories import list_categories
from app.services.sfx_ambient.models import SfxJob


def index_job(job: SfxJob) -> list[str]:
    ids: list[str] = []
    for i, layer in enumerate(job.layers):
        lid = layer.library_id or f"sfxlib_{job.job_id}_{i}"
        layer.library_id = lid
        store.put_library_entry(
            lid,
            {
                "library_id": lid,
                "job_id": job.job_id,
                "kind": layer.kind,
                "category": layer.category,
                "categories": [layer.category],
                "volume": layer.volume,
                "duration_sec": max(0.0, layer.end_sec - layer.start_sec),
                "loop": layer.loop,
                "asset_url": layer.asset_url,
                "environment": job.environment.environment,
                "audio_version": job.audio_version,
            },
        )
        ids.append(lid)
    job.library_ids = ids
    return ids


def library_payload(
    *,
    kind: str | None = None,
    category: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    return {
        "items": store.list_library(kind=kind, category=category, limit=limit),
        "count": len(store.list_library(kind=kind, category=category, limit=limit)),
        "categories": list_categories(kind=kind),
    }


def sfx_catalog_payload() -> dict[str, Any]:
    return {
        "categories": list_categories(kind="sfx") + [
            c for c in list_categories() if c["kind"] in ("foley", "both")
        ],
        "kind": "sfx",
    }


def ambient_catalog_payload() -> dict[str, Any]:
    return {
        "categories": list_categories(kind="ambient") + [
            c for c in list_categories() if c["kind"] == "both"
        ],
        "kind": "ambient",
    }
