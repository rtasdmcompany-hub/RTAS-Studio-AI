"""RTAS Studio AI — Project Management & Collaboration Engine (Phase 7 Sprint 4)."""

from app.services.project_collaboration.engine import (
    ProjectCollaborationService,
    get_engine,
    get_project_collaboration_service,
    reset_engine,
)
from app.services.project_collaboration.version import (
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
    "ProjectCollaborationService",
    "get_engine",
    "get_project_collaboration_service",
    "reset_engine",
]
