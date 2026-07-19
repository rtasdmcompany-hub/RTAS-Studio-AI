"""Phase 10 Sprint 7 — Observability & Operational Excellence."""

from importlib import import_module

from app.services.phase10_observability.version import (
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
    "Phase10ObservabilityService",
    "get_phase10_observability_service",
    "reset_phase10_observability_service",
]

_LAZY = {
    "Phase10ObservabilityService": (
        "app.services.phase10_observability.service",
        "Phase10ObservabilityService",
    ),
    "get_phase10_observability_service": (
        "app.services.phase10_observability.service",
        "get_phase10_observability_service",
    ),
    "reset_phase10_observability_service": (
        "app.services.phase10_observability.service",
        "reset_phase10_observability_service",
    ),
}


def __getattr__(name: str):
    spec = _LAZY.get(name)
    if spec is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    mod = import_module(spec[0])
    return getattr(mod, spec[1])
