"""Character Registry — Character_A / Character_B / Character_C."""

from __future__ import annotations

import threading
from typing import Any

from app.services.character_generation.models import CharacterRecord, RegistrySlot

_lock = threading.Lock()
_slots: dict[RegistrySlot, CharacterRecord | None] = {
    "Character_A": None,
    "Character_B": None,
    "Character_C": None,
}
_by_id: dict[str, CharacterRecord] = {}


def register(
    record: CharacterRecord,
    *,
    slot: RegistrySlot | None = None,
) -> CharacterRecord:
    with _lock:
        resolved = slot or record.registry_slot
        if resolved not in _slots:
            # Auto-assign first empty slot
            for candidate in ("Character_A", "Character_B", "Character_C"):
                if _slots[candidate] is None:  # type: ignore[index]
                    resolved = candidate  # type: ignore[assignment]
                    break
            else:
                resolved = "Character_A"
        record.registry_slot = resolved  # type: ignore[assignment]
        _slots[resolved] = record  # type: ignore[index]
        _by_id[record.character_id] = record
        return record


def get(character_id: str) -> CharacterRecord | None:
    with _lock:
        return _by_id.get(character_id)


def get_slot(slot: RegistrySlot) -> CharacterRecord | None:
    with _lock:
        return _slots.get(slot)


def list_registered() -> list[CharacterRecord]:
    with _lock:
        return [r for r in _slots.values() if r is not None]


def list_all() -> list[CharacterRecord]:
    with _lock:
        return list(_by_id.values())


def registry_payload() -> dict[str, Any]:
    with _lock:
        return {
            "slots": {
                slot: (rec.summary() if rec else None)
                for slot, rec in _slots.items()
            },
            "count": sum(1 for r in _slots.values() if r is not None),
            "characters": [r.summary() for r in _by_id.values()],
        }


def clear() -> None:
    with _lock:
        _slots["Character_A"] = None
        _slots["Character_B"] = None
        _slots["Character_C"] = None
        _by_id.clear()
