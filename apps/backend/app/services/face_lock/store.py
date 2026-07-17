"""In-memory face lock store — persistent per character_id."""

from __future__ import annotations

import threading
from collections import OrderedDict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.face_lock.models import FaceLockRecord

_lock = threading.Lock()
_by_character: OrderedDict[str, "FaceLockRecord"] = OrderedDict()
_by_lock_id: OrderedDict[str, "FaceLockRecord"] = OrderedDict()
_MAX = 2000


def save(record: "FaceLockRecord") -> "FaceLockRecord":
    with _lock:
        _by_character[record.character_id] = record
        _by_lock_id[record.lock_id] = record
        while len(_by_character) > _MAX:
            old_cid, old = _by_character.popitem(last=False)
            _by_lock_id.pop(old.lock_id, None)
        return record


def get_by_character(character_id: str) -> "FaceLockRecord | None":
    with _lock:
        return _by_character.get(character_id)


def get_by_lock_id(lock_id: str) -> "FaceLockRecord | None":
    with _lock:
        return _by_lock_id.get(lock_id)


def list_locks(limit: int = 50) -> list["FaceLockRecord"]:
    with _lock:
        items = list(_by_character.values())
    return list(reversed(items[-max(1, min(500, limit)) :]))


def clear() -> None:
    with _lock:
        _by_character.clear()
        _by_lock_id.clear()
