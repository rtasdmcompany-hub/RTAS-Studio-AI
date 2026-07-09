from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from app.core.config import reload_settings, settings
from app.schemas.generation import (
    GenerateAsyncResponse,
    GenerateRequest,
    GenerateResponse,
)
from app.services.ai_service import LiveGenerationError, run_generation
from app.services.tier_fal_routing import (
    BillingAccessError,
    assert_billing_for_live_generation,
)
from app.services.content_moderation import (
    CONTENT_POLICY_MESSAGE,
    ContentPolicyViolation,
    assert_generate_request_allowed,
    log_content_policy_violation,
)
from app.services.fal_guard import assert_fal_live_allowed
from app.services.generation_lock import (
    GenerationInProgressError,
    acquire_generation_slot,
    release_generation_slot,
)
from app.services.trial_abuse import FREE_TRIAL_ABUSE_MESSAGE, is_free_trial_blocked

router = APIRouter(prefix="/generate", tags=["generation"])


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return ""


@router.post("", response_model=GenerateResponse, response_model_by_alias=True)
async def create_generation(body: GenerateRequest, request: Request) -> GenerateResponse:
    """
    Ingest studio payload → AI service layer → delivery URL for frontend player.
    """
    try:
        assert_generate_request_allowed(body)
    except ContentPolicyViolation as exc:
        log_content_policy_violation(
            user_id=body.user_id,
            device_fingerprint=body.device_fingerprint,
            ip_address=_client_ip(request),
            category=body.category,
            job_id=body.job_id,
            matched_terms=exc.matched,
            reason=exc.reason,
            route="/api/generate",
            preview_only=body.preview_only,
        )
        raise HTTPException(status_code=403, detail=CONTENT_POLICY_MESSAGE) from exc

    if body.visual_style == "real":
        consent = (body.fields.get("faceConsent") or "").strip().upper()
        has_face = "faceReference" in body.files
        if consent != "YES" or not has_face:
            raise HTTPException(
                status_code=400,
                detail="Real face mode requires faceReference file and faceConsent YES",
            )

    if body.use_free_trial:
        profile = body.profile
        account_used = False
        user_id = body.user_id or "local-user"
        if profile:
            account_used = bool(
                profile.has_used_free_trial or profile.free_trial_used
            )
        blocked, _reason = is_free_trial_blocked(
            user_id=user_id,
            ip_address=_client_ip(request),
            device_fingerprint=body.device_fingerprint,
            account_trial_used=account_used,
        )
        if blocked:
            raise HTTPException(status_code=403, detail=FREE_TRIAL_ABUSE_MESSAGE)

    reload_settings()
    # Preview renders never hit Fal — protects owner wallet and keeps UX smooth.
    if (
        settings.fal_configured
        and settings.fal_live_enabled
        and not body.preview_only
        and not body.use_free_trial
    ):
        try:
            assert_billing_for_live_generation(body)
        except BillingAccessError as exc:
            raise HTTPException(status_code=402, detail=exc.message) from exc
        try:
            assert_fal_live_allowed(body.user_id)
        except ValueError as exc:
            msg = str(exc)
            print(f"Fal API Error: {msg}", flush=True)
            if "balance" in msg.lower() or "billing" in msg.lower() or "wait" in msg.lower():
                raise HTTPException(status_code=402, detail=msg) from exc
            raise HTTPException(status_code=503, detail=msg) from exc

    try:
        await acquire_generation_slot()
    except GenerationInProgressError as exc:
        print(f"Generation conflict: {exc.message}", flush=True)
        raise HTTPException(status_code=409, detail=exc.message) from exc

    try:
        result = await run_generation(body)
    except ContentPolicyViolation as exc:
        log_content_policy_violation(
            user_id=body.user_id,
            device_fingerprint=body.device_fingerprint,
            ip_address=_client_ip(request),
            category=body.category,
            job_id=body.job_id,
            matched_terms=exc.matched,
            reason=exc.reason,
            route="/api/generate",
            preview_only=body.preview_only,
        )
        raise HTTPException(status_code=403, detail=CONTENT_POLICY_MESSAGE) from exc
    except LiveGenerationError as exc:
        print(f"Fal API Error: {exc.message}", flush=True)
        if exc.error_code == "model_routing":
            raise HTTPException(status_code=422, detail=exc.message) from exc
        if exc.error_code == "billing_required":
            raise HTTPException(status_code=402, detail=exc.message) from exc
        if exc.error_code in ("fal_auth", "replicate_auth"):
            raise HTTPException(status_code=401, detail=exc.message) from exc
        if exc.error_code in ("fal_credit", "replicate_credit"):
            raise HTTPException(status_code=402, detail=exc.message) from exc
        raise HTTPException(status_code=502, detail=exc.message) from exc
    except Exception as exc:
        print(f"Fal API Error: {exc}", flush=True)
        raise
    finally:
        await release_generation_slot()

    storage_key = f"outputs/{result.job_id}.mp4" if result.local_mp4_path else None
    asset_path = str(result.local_mp4_path) if result.local_mp4_path else None

    return GenerateResponse(
        ok=True,
        job_id=result.job_id,
        steps=result.steps,
        provider=result.provider,
        prompt_preview=result.prompt_preview,
        credits_used=result.credits_used,
        preview_only=result.preview_only,
        can_download=result.can_download,
        video_url=result.delivery_url,
        duration_seconds=result.duration_seconds,
        message=result.message,
        simulation_mode=result.simulation_mode,
        asset_path=asset_path,
        storage_key=storage_key,
    )


async def _run_generation_background(body: GenerateRequest) -> None:
    """Long-running multiclip pipeline — must not block the HTTP response."""
    from app.services.job_progress import PipelineProgressReporter

    progress: PipelineProgressReporter | None = None
    if body.status_callback_url and body.pipeline_job_id:
        progress = PipelineProgressReporter(
            body.status_callback_url,
            body.pipeline_job_id,
        )

    try:
        await acquire_generation_slot()
        await run_generation(body)
    except LiveGenerationError as exc:
        if progress:
            await progress.failed(exc.message)
        print(f"Async generation failed: {exc.message}", flush=True)
    except Exception as exc:
        if progress:
            await progress.failed(str(exc))
        print(f"Async generation error: {exc}", flush=True)
    finally:
        await release_generation_slot()


@router.post(
    "/async",
    response_model=GenerateAsyncResponse,
    response_model_by_alias=True,
    status_code=202,
)
async def create_generation_async(
    body: GenerateRequest,
    request: Request,
    background_tasks: BackgroundTasks,
) -> GenerateAsyncResponse:
    """
    Queue a long render on the GPU worker without blocking the gateway (avoids 504).
    Pipeline status is PATCHed to statusCallbackUrl while chunks render and stitch.
    """
    try:
        assert_generate_request_allowed(body)
    except ContentPolicyViolation as exc:
        log_content_policy_violation(
            user_id=body.user_id,
            device_fingerprint=body.device_fingerprint,
            ip_address=_client_ip(request),
            category=body.category,
            job_id=body.job_id,
            matched_terms=exc.matched,
            reason=exc.reason,
            route="/api/generate/async",
            preview_only=body.preview_only,
        )
        raise HTTPException(status_code=403, detail=CONTENT_POLICY_MESSAGE) from exc

    if body.visual_style == "real":
        consent = (body.fields.get("faceConsent") or "").strip().upper()
        has_face = "faceReference" in body.files
        if consent != "YES" or not has_face:
            raise HTTPException(
                status_code=400,
                detail="Real face mode requires faceReference file and faceConsent YES",
            )

    reload_settings()
    if (
        settings.fal_configured
        and settings.fal_live_enabled
        and not body.preview_only
        and not body.use_free_trial
    ):
        try:
            assert_billing_for_live_generation(body)
        except BillingAccessError as exc:
            raise HTTPException(status_code=402, detail=exc.message) from exc
        try:
            assert_fal_live_allowed(body.user_id)
        except ValueError as exc:
            msg = str(exc)
            if "balance" in msg.lower() or "billing" in msg.lower() or "wait" in msg.lower():
                raise HTTPException(status_code=402, detail=msg) from exc
            raise HTTPException(status_code=503, detail=msg) from exc

    background_tasks.add_task(_run_generation_background, body)
    job_id = body.pipeline_job_id or body.job_id or "pending"
    return GenerateAsyncResponse(
        job_id=job_id,
        status="queued",
        message="Long render queued — track status via pipeline job grid",
    )


@router.get("/health")
async def generate_health():
    return {"status": "ok", "service": "generate"}


@router.get("/cost-policy")
async def generate_cost_policy(duration_seconds: int = 30):
    """Weighted deduction preview for studio generate flow."""
    from app.services.model_routing import get_cost_policy_payload

    return get_cost_policy_payload(duration_seconds)
