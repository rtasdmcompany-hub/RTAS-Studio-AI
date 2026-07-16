"""Job / scene / shot metadata store + generation history."""

from __future__ import annotations

import threading
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.services.text_to_video.models import (
    HistoryRecord,
    SceneMetadata,
    ShotMetadata,
    TextToVideoJob,
)

_lock = threading.Lock()
_jobs: OrderedDict[str, TextToVideoJob] = OrderedDict()
_scenes: OrderedDict[str, SceneMetadata] = OrderedDict()
_shots: OrderedDict[str, ShotMetadata] = OrderedDict()
_history: list[HistoryRecord] = []
_MAX_JOBS = 500
_MAX_HISTORY = 5000


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MetadataStore:
    def save_job(self, job: TextToVideoJob) -> TextToVideoJob:
        with _lock:
            job.updated_at = _now()
            _jobs[job.job_id] = job
            for scene in job.scenes:
                _scenes[scene.scene_id] = scene
            for shot in job.shots:
                _shots[shot.shot_id] = shot
            while len(_jobs) > _MAX_JOBS:
                old_id, old = _jobs.popitem(last=False)
                for s in old.scenes:
                    _scenes.pop(s.scene_id, None)
                for sh in old.shots:
                    _shots.pop(sh.shot_id, None)
            return job

    def get_job(self, job_id: str) -> TextToVideoJob | None:
        with _lock:
            job = _jobs.get(job_id)
            if not job:
                return None
            # Return a copy via dict round-trip-ish shallow rebuild
            return job

    def get_scene(self, scene_id: str) -> SceneMetadata | None:
        with _lock:
            return _scenes.get(scene_id)

    def get_shot(self, shot_id: str) -> ShotMetadata | None:
        with _lock:
            return _shots.get(shot_id)

    def list_jobs(self, limit: int = 50) -> list[TextToVideoJob]:
        with _lock:
            return list(_jobs.values())[-limit:]

    def update_job_state(self, job_id: str, state: str, **metadata: Any) -> TextToVideoJob | None:
        with _lock:
            job = _jobs.get(job_id)
            if not job:
                return None
            job.state = state  # type: ignore[assignment]
            job.updated_at = _now()
            if metadata:
                job.metadata.update(metadata)
            return job


class HistoryStore:
    def append(
        self,
        *,
        job_id: str,
        event: str,
        request_id: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> HistoryRecord:
        with _lock:
            record = HistoryRecord(
                history_id=f"hist_{uuid4().hex[:12]}",
                job_id=job_id,
                request_id=request_id,
                event=event,
                timestamp=_now(),
                detail=detail or {},
            )
            _history.append(record)
            while len(_history) > _MAX_HISTORY:
                _history.pop(0)
            return record

    def for_job(self, job_id: str, limit: int = 200) -> list[HistoryRecord]:
        with _lock:
            items = [h for h in _history if h.job_id == job_id]
            return items[-limit:]

    def recent(self, limit: int = 100) -> list[HistoryRecord]:
        with _lock:
            return list(_history[-limit:])

    def clear(self) -> None:
        with _lock:
            _history.clear()


metadata_store = MetadataStore()
history_store = HistoryStore()


def clear_all_stores() -> None:
    with _lock:
        _jobs.clear()
        _scenes.clear()
        _shots.clear()
        _history.clear()
