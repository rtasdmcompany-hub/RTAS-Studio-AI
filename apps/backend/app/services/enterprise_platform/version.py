"""RTAS Studio AI Enterprise AI Orchestration Platform — Phase 6 Final Release."""

PLATFORM_NAME = "RTAS Studio AI Enterprise AI Orchestration Platform"
PLATFORM_VERSION = "1.0.0"
PLATFORM_LABEL = f"{PLATFORM_NAME} v{PLATFORM_VERSION}"
ENGINE_NAME = PLATFORM_NAME
ENGINE_VERSION = PLATFORM_VERSION
ENGINE_LABEL = PLATFORM_LABEL
PHASE = 6
SPRINT = 10
RELEASE_STATUS = "RELEASED"

REQUIRED_PROVIDERS: tuple[str, ...] = (
    "openai",
    "gemini",
    "claude",
    "runpod",
    "stability",
    "elevenlabs",
)

INTEGRATED_ENGINES: tuple[str, ...] = (
    "provider_manager",
    "connector_framework",
    "ai_router",
    "cost_optimizer",
    "memory_engine",
    "context_engine",
    "workflow_engine",
    "security_engine",
    "compliance_engine",
    "monitoring_engine",
    "self_healing_engine",
    "queue_manager",
)

QUALITY_PASS_THRESHOLD = 90.0
