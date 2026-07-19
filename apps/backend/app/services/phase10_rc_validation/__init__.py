"""Phase 10 Sprint 5 — AI QA & Release Candidate (RC-1) Validation."""

from app.services.phase10_rc_validation.service import (
    Phase10RcValidationService,
    get_phase10_rc_validation_service,
    reset_phase10_rc_validation_service,
)
from app.services.phase10_rc_validation.version import (
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
    "Phase10RcValidationService",
    "get_phase10_rc_validation_service",
    "reset_phase10_rc_validation_service",
]
