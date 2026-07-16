"""Multi AI Video Generation Engine — public API."""

from app.services.multi_ai.engine import MultiAIVideoEngine, get_multi_ai_engine
from app.services.multi_ai.models import GenerationFlowResult, QueueJob
from app.services.multi_ai.registry import (
    DEFAULT_FAILOVER_ORDER,
    build_provider_registry,
    detect_available_providers,
    provider_compatibility_matrix,
)

__all__ = [
    "MultiAIVideoEngine",
    "get_multi_ai_engine",
    "GenerationFlowResult",
    "QueueJob",
    "DEFAULT_FAILOVER_ORDER",
    "build_provider_registry",
    "detect_available_providers",
    "provider_compatibility_matrix",
]
