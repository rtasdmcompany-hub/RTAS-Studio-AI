"""RTAS Studio AI — AI Face Lock & Identity Engine (Phase 5 Sprint 2)."""

from app.services.face_lock.engine import (
    get_identity,
    lock_character,
    lock_dict,
    verify_dict,
    verify_identity,
)
from app.services.face_lock import store
from app.services.face_lock.models import PRESERVED_TRAITS
from app.services.face_lock.version import (
    DRIFT_THRESHOLD,
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
)

__all__ = [
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "ENGINE_LABEL",
    "DRIFT_THRESHOLD",
    "PRESERVED_TRAITS",
    "lock_character",
    "lock_dict",
    "verify_identity",
    "verify_dict",
    "get_identity",
    "store",
]
