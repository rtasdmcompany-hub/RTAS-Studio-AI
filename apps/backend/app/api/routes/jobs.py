"""Provider job status / cancel endpoints for the AI orchestrator."""

from fastapi import APIRouter, HTTPException

from app.services.ai_service import LiveGenerationError
from app.services.orchestrator import provider_cancel, provider_status

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{provider}/{external_job_id}/status")
async def get_provider_job_status(provider: str, external_job_id: str):
    try:
        status = await provider_status(provider, external_job_id)
    except LiveGenerationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "provider": status.provider,
        "externalJobId": status.external_job_id,
        "status": status.status,
        "progressPercent": status.progress_percent,
        "error": status.error,
        "remoteUrl": status.remote_url,
        "metadata": status.metadata,
    }


@router.post("/{provider}/{external_job_id}/cancel")
async def cancel_provider_job(provider: str, external_job_id: str):
    ok = await provider_cancel(provider, external_job_id)
    if not ok:
        raise HTTPException(
            status_code=409,
            detail="Provider did not accept cancel (unsupported or already terminal)",
        )
    return {"ok": True, "provider": provider, "externalJobId": external_job_id}
