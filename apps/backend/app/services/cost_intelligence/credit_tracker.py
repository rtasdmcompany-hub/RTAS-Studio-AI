"""Credit Usage Tracker."""

from __future__ import annotations

import threading

_lock = threading.Lock()
_by_provider: dict[str, float] = {}
_by_project: dict[str, float] = {}
_by_team: dict[str, float] = {}
_total: float = 0.0


def record(
    provider: str,
    credits: float,
    *,
    project_id: str | None = None,
    team_id: str | None = None,
) -> float:
    global _total
    n = max(0.0, float(credits))
    key = (provider or "unknown").lower()
    with _lock:
        _by_provider[key] = _by_provider.get(key, 0.0) + n
        if project_id:
            _by_project[project_id] = _by_project.get(project_id, 0.0) + n
        if team_id:
            _by_team[team_id] = _by_team.get(team_id, 0.0) + n
        _total += n
        return _by_provider[key]


def summary() -> dict[str, object]:
    with _lock:
        return {
            "total_credits": round(_total, 4),
            "by_provider": {k: round(v, 4) for k, v in _by_provider.items()},
            "by_project": {k: round(v, 4) for k, v in _by_project.items()},
            "by_team": {k: round(v, 4) for k, v in _by_team.items()},
        }


def clear() -> None:
    global _total
    with _lock:
        _by_provider.clear()
        _by_project.clear()
        _by_team.clear()
        _total = 0.0
