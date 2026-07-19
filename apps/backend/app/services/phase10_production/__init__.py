"""Phase 10 Sprint 9 — Production Environment & RC-2."""

from importlib import import_module

from app.services.phase10_production.version import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    PHASE,
    PHASE_STATUS,
    RC_LABEL,
    SPRINT,
)

__all__ = [
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "ENGINE_LABEL",
    "PHASE",
    "SPRINT",
    "RC_LABEL",
    "PHASE_STATUS",
    "Phase10ProductionService",
    "get_phase10_production_service",
    "reset_phase10_production_service",
]

_LAZY = {
    "Phase10ProductionService": (
        "app.services.phase10_production.service",
        "Phase10ProductionService",
    ),
    "get_phase10_production_service": (
        "app.services.phase10_production.service",
        "get_phase10_production_service",
    ),
    "reset_phase10_production_service": (
        "app.services.phase10_production.service",
        "reset_phase10_production_service",
    ),
}


def __getattr__(name: str):
    spec = _LAZY.get(name)
    if spec is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    mod = import_module(spec[0])
    return getattr(mod, spec[1])
