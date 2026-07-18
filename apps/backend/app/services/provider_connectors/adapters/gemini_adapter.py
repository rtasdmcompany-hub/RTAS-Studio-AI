"""Google Gemini connector adapter."""

from __future__ import annotations

from app.services.provider_connectors.auth import require_auth_or_placeholder
from app.services.provider_connectors.base import BaseProviderConnector
from app.services.provider_connectors.models import StandardRequest, StandardResponse


class GeminiConnector(BaseProviderConnector):
    provider_id = "gemini"
    display_name = "Google Gemini"
    version = "1.0.0-connector"
    capabilities = ("text", "image", "video", "audio", "embedding", "vision", "translation")
    default_priority = 20

    async def _invoke(self, request: StandardRequest) -> StandardResponse:
        live, _key = require_auth_or_placeholder(self.config)
        if not live:
            return self._placeholder_response(request)
        return StandardResponse(
            provider=self.provider_id,
            success=True,
            capability=request.capability,
            data={
                "mode": "configured",
                "model": request.model or self.config.default_model,
                "message": "Gemini connector ready (live invoke deferred)",
                "prompt_chars": len(request.prompt or ""),
            },
            provider_version=self.detect_version(),
            metadata={"placeholder": False, "live_invoke": False},
        )
