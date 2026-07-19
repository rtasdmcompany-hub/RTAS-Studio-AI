"""AI Job Orchestration Engine — Phase 6 Sprint 4 (+ Phase 10 Sprint 4 scale)."""

ENGINE_NAME = "RTAS AI Job Orchestration Engine"
ENGINE_VERSION = "1.1.0"
ENGINE_LABEL = f"{ENGINE_NAME} v{ENGINE_VERSION}"
PHASE = 6
SPRINT = 4
DEFAULT_MAX_CONCURRENT = 8
DEFAULT_TIMEOUT_SEC = 120.0
MAX_RETRIES = 3
# Backpressure: reject new enqueue when queued work exceeds this depth.
MAX_QUEUE_DEPTH = 5000
