"""In-memory appearance store — persistent per character_id."""

from __future__ import annotations

import threading
from collections import OrderedDict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.appearance.models import AppearanceRecord

_lock = threading.Lock()
_by_character: OrderedDict[str, "AppearanceRecord"] = OrderedDict()
_by_profile_id: OrderedDict[str, "AppearanceRecord"] = OrderedDict()
_MAX = 2000


def save(record: "AppearanceRecord") -> "AppearanceRecord":
    with _lock:
        _by_character[record.character_id] = record
        _by_profile_id[record.profile_id] = record
        while len(_by_character) > _MAX:
            _cid, old = _by_character.popitem(last=False)
            _by_profile_id.pop(old.profile_id, None)
        return record


def get_by_character(character_id: str) -> "AppearanceRecord | None":
    with _lock:
        return _by_character.get(character_id)


def get_by_profile_id(profile_id: str) -> "AppearanceRecord | None":
    with _lock:
        return _by_profile_id.get(profile_id)


def list_profiles(limit: int = 50) -> list["AppearanceRecord"]:
    with _lock:
        items = list(_by_character.values())
    return list(reversed(items[-max(1, min(500, limit)) :]))


def clear() -> None:
    with _lock:
        _by_character.clear()
        _by_profile_id.clear()
