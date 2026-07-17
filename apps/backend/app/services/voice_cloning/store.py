"""In-memory store for clones, character voices, versions, training history."""

from __future__ import annotations

import threading
from collections import OrderedDict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.voice_cloning.models import CharacterVoiceProfile, VoiceCloneJob

_lock = threading.Lock()
_CLONES: OrderedDict[str, "VoiceCloneJob"] = OrderedDict()
_HISTORY: OrderedDict[str, list[dict]] = OrderedDict()
_CHARACTERS: OrderedDict[str, "CharacterVoiceProfile"] = OrderedDict()
_CHECKSUMS: set[str] = set()
_MAX = 2000


def put_clone(job: "VoiceCloneJob") -> "VoiceCloneJob":
    with _lock:
        _CLONES[job.clone_id] = job
        hist = _HISTORY.setdefault(job.clone_id, [])
        hist.append(
            {
                "version": len(hist) + 1,
                "state": job.state,
                "summary": job.summary(),
            }
        )
        job.history = list(hist)
        job.metadata["version"] = len(hist)
        if job.reference_checksum:
            _CHECKSUMS.add(job.reference_checksum)
        while len(_CLONES) > _MAX:
            old_id, _ = _CLONES.popitem(last=False)
            _HISTORY.pop(old_id, None)
        return job


def get_clone(clone_id: str) -> "VoiceCloneJob | None":
    with _lock:
        return _CLONES.get(clone_id)


def list_clone_history(limit: int = 50) -> list[dict]:
    with _lock:
        items = list(_CLONES.values())[-limit:]
        return [j.summary() for j in reversed(items)]


def get_clone_history(clone_id: str) -> list[dict]:
    with _lock:
        return list(_HISTORY.get(clone_id, []))


def known_checksums() -> set[str]:
    with _lock:
        return set(_CHECKSUMS)


def put_character(profile: "CharacterVoiceProfile") -> "CharacterVoiceProfile":
    with _lock:
        _CHARACTERS[profile.character_id] = profile
        return profile


def get_character(character_id: str) -> "CharacterVoiceProfile | None":
    with _lock:
        return _CHARACTERS.get(character_id)


def list_characters(limit: int = 100) -> list["CharacterVoiceProfile"]:
    with _lock:
        return list(_CHARACTERS.values())[-limit:]


def clear() -> None:
    with _lock:
        _CLONES.clear()
        _HISTORY.clear()
        _CHARACTERS.clear()
        _CHECKSUMS.clear()
