"""OpenAI connector adapter (placeholder when OPENAI_API_KEY missing)."""

from __future__ import annotations

from app.services.provider_connectors.auth import require_auth_or_placeholder
from app.services.provider_connectors.base import BaseProviderConnector
from app.services.provider_connectors.models import StandardRequest, StandardResponse


class OpenAIConnector(BaseProviderConnector):
    provider_id = "openai"
    display_name = "OpenAI"
    version = "1.0.0-connector"
    capabilities = ("text", "image", "audio", "embedding", "vision", "translation")
    default_priority = 10

    async def _invoke(self, request: StandardRequest) -> StandardResponse:
        live, _key = require_auth_or_placeholder(self.config)
        if not live:
            return self._placeholder_response(request)
        # Live path reserved — no hard dependency on SDK in Sprint 2 foundation
        return StandardResponse(
            provider=self.provider_id,
            success=True,
            capability=request.capability,
            data={
                "mode": "configured",
                "model": request.model or self.config.default_model,
                "message": "OpenAI connector ready (live invoke deferred to orchestration sprint)",
                "prompt_chars": len(request.prompt or ""),
            },
            provider_version=self.detect_version(),
            metadata={"placeholder": False, "live_invoke": False},
        )
