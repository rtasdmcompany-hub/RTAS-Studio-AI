"""ElevenLabs voice/audio connector adapter."""

from __future__ import annotations

from app.services.provider_connectors.auth import require_auth_or_placeholder
from app.services.provider_connectors.base import BaseProviderConnector
from app.services.provider_connectors.models import StandardRequest, StandardResponse


class ElevenLabsConnector(BaseProviderConnector):
    provider_id = "elevenlabs"
    display_name = "ElevenLabs"
    version = "1.0.0-connector"
    capabilities = ("voice", "audio", "music")
    default_priority = 25

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
                "message": "ElevenLabs connector ready (live invoke deferred)",
                "prompt_chars": len(request.prompt or ""),
            },
            provider_version=self.detect_version(),
            metadata={"placeholder": False, "live_invoke": False},
        )
