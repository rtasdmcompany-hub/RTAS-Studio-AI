"""Timeline export packaging."""

from __future__ import annotations

from typing import Any

from app.services.audio_timeline.models import TimelineJob


def build_export_payload(job: TimelineJob) -> dict[str, Any]:
    return {
        "format": "rtas-timeline-v1",
        "job_id": job.job_id,
        "duration_sec": job.duration_sec,
        "fps": job.fps,
        "sync_accuracy": job.sync.sync_accuracy,
        "tracks": [t.to_dict() for t in job.tracks],
        "layers": [layer.to_dict() for layer in job.layers],
        "beat_markers": [b.to_dict() for b in job.beat_markers],
        "sync": job.sync.to_dict(),
        "export_url": job.export_url or f"/media/timeline/{job.job_id}/master.json",
        "master_timeline_url": job.master_timeline_url
        or f"/media/timeline/{job.job_id}/master.timeline",
        "production_ready": job.production_ready,
        "version": job.timeline_version,
    }
