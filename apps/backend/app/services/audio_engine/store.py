"""In-memory store for Audio Engine plans + version history."""

from __future__ import annotations

import threading
from collections import OrderedDict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.audio_engine.models import AudioEnginePlan

_lock = threading.Lock()
_PLANS: OrderedDict[str, "AudioEnginePlan"] = OrderedDict()
_HISTORY: OrderedDict[str, list[dict]] = OrderedDict()
_MAX = 2000


def put_plan(plan: "AudioEnginePlan") -> "AudioEnginePlan":
    with _lock:
        _PLANS[plan.job_id] = plan
        hist = _HISTORY.setdefault(plan.job_id, [])
        hist.append(
            {
                "version": plan.metadata.version,
                "state": plan.state,
                "production_ready": plan.production_ready,
                "summary": plan.summary(),
            }
        )
        plan.history = list(hist)
        while len(_PLANS) > _MAX:
            old_id, _ = _PLANS.popitem(last=False)
            _HISTORY.pop(old_id, None)
        return plan


def get_plan(job_id: str) -> "AudioEnginePlan | None":
    with _lock:
        return _PLANS.get(job_id)


def get_history(job_id: str) -> list[dict]:
    with _lock:
        return list(_HISTORY.get(job_id, []))


def clear() -> None:
    with _lock:
        _PLANS.clear()
        _HISTORY.clear()
