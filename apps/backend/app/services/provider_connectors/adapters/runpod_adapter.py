"""RunPod GPU connector adapter."""

from __future__ import annotations

from app.services.provider_connectors.auth import require_auth_or_placeholder
from app.services.provider_connectors.base import BaseProviderConnector
from app.services.provider_connectors.models import StandardRequest, StandardResponse


class RunPodConnector(BaseProviderConnector):
    provider_id = "runpod"
    display_name = "RunPod"
    version = "1.0.0-connector"
    capabilities = ("image", "video", "audio")
    default_priority = 40

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
                "message": "RunPod connector ready (live invoke deferred)",
                "prompt_chars": len(request.prompt or ""),
            },
            provider_version=self.detect_version(),
            metadata={"placeholder": False, "live_invoke": False},
        )
