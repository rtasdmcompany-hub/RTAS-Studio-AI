"""Phase 10 Sprint 6 — Disaster Recovery & High Availability."""

from importlib import import_module

from app.services.phase10_disaster_recovery.version import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    PHASE,
    SPRINT,
)

__all__ = [
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "ENGINE_LABEL",
    "PHASE",
    "SPRINT",
    "Phase10DisasterRecoveryService",
    "get_phase10_disaster_recovery_service",
    "reset_phase10_disaster_recovery_service",
    "backup_store",
]

_LAZY = {
    "Phase10DisasterRecoveryService": (
        "app.services.phase10_disaster_recovery.service",
        "Phase10DisasterRecoveryService",
    ),
    "get_phase10_disaster_recovery_service": (
        "app.services.phase10_disaster_recovery.service",
        "get_phase10_disaster_recovery_service",
    ),
    "reset_phase10_disaster_recovery_service": (
        "app.services.phase10_disaster_recovery.service",
        "reset_phase10_disaster_recovery_service",
    ),
    "backup_store": (
        "app.services.phase10_disaster_recovery.backup_store",
        None,
    ),
}


def __getattr__(name: str):
    spec = _LAZY.get(name)
    if spec is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    mod_name, attr = spec
    mod = import_module(mod_name)
    return mod if attr is None else getattr(mod, attr)
