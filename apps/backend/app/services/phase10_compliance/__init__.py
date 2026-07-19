"""Phase 10 Sprint 8 — Legal Compliance & Enterprise Release Readiness."""

from importlib import import_module

from app.services.phase10_compliance.version import (
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
    "Phase10ComplianceService",
    "get_phase10_compliance_service",
    "reset_phase10_compliance_service",
]

_LAZY = {
    "Phase10ComplianceService": (
        "app.services.phase10_compliance.service",
        "Phase10ComplianceService",
    ),
    "get_phase10_compliance_service": (
        "app.services.phase10_compliance.service",
        "get_phase10_compliance_service",
    ),
    "reset_phase10_compliance_service": (
        "app.services.phase10_compliance.service",
        "reset_phase10_compliance_service",
    ),
}


def __getattr__(name: str):
    spec = _LAZY.get(name)
    if spec is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    mod = import_module(spec[0])
    return getattr(mod, spec[1])
