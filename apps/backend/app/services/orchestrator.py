"""
Central GPU-worker AI Orchestrator.

Validates → selects provider → generate → progress webhooks → deliver.
Studio never imports Fal/Replicate SDKs — only this layer does.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from app.schemas.generation import GenerateRequest
from app.services.ai_service import (
    GenerationJobResult,
    LiveGenerationError,
    run_generation,
)
from app.services.multi_ai import build_provider_registry, get_multi_ai_engine
from app.services.providers.base import BaseAIProvider

logger = logging.getLogger(__name__)


def _structured(
    event: str,
    *,
    generation_id: str | None = None,
    user_id: str | None = None,
    provider: str | None = None,
    duration_seconds: int | None = None,
    credits: int | None = None,
    latency_ms: float | None = None,
    failure: str | None = None,
    **extra: Any,
) -> None:
    payload = {
        "event": event,
        "generation_id": generation_id,
        "user_id": user_id,
        "provider": provider,
        "duration_seconds": duration_seconds,
        "credits": credits,
        "latency_ms": latency_ms,
        "failure": failure,
        **extra,
    }
    line = " ".join(f"{k}={v!r}" for k, v in payload.items() if v is not None)
    if failure:
        logger.error("orchestrator %s", line)
    else:
        logger.info("orchestrator %s", line)


def get_provider_adapters() -> dict[str, BaseAIProvider]:
    return build_provider_registry()


def select_live_provider() -> BaseAIProvider | None:
    engine = get_multi_ai_engine()
    name = engine.select_provider()
    if not name:
        return None
    return engine.registry.get(name)


async def orchestrate_generation(body: GenerateRequest) -> GenerationJobResult:
    """
    Production entrypoint for /api/generate.
    Wraps run_generation with structured logging and provider selection telemetry.
    """
    started = time.perf_counter()
    generation_id = body.job_id or body.pipeline_job_id
    user_id = body.user_id
    selected = select_live_provider()

    _structured(
        "start",
        generation_id=generation_id,
        user_id=user_id,
        provider=selected.name if selected else None,
        duration_seconds=body.duration_seconds,
    )

    if (
        not body.preview_only
        and not body.use_free_trial
        and selected is None
    ):
        raise LiveGenerationError(
            "No live AI provider configured. Set FAL_KEY or REPLICATE_API_TOKEN.",
            error_code="provider_not_configured",
        )

    # Real AI intelligence stack (backend only — no UI changes).
    try:
        from app.services.intelligence.pipeline import run_intelligence_pipeline

        raw_prompt = (
            (body.fields or {}).get("directionPrompt")
            or (body.fields or {}).get("mainPrompt")
            or (body.fields or {}).get("prompt")
            or ""
        )
        ref_urls: list[str] = []
        files = getattr(body, "files", None) or {}
        for key in ("faceReference", "sourceImage", "imageReference"):
            meta = files.get(key) if isinstance(files, dict) else None
            if meta is None:
                continue
            if isinstance(meta, dict):
                url = meta.get("url") or meta.get("localPath") or meta.get("local_path")
            else:
                url = getattr(meta, "url", None) or getattr(meta, "local_path", None)
            if isinstance(url, str) and url.strip():
                ref_urls.append(url.strip())

        plan = run_intelligence_pipeline(
            raw_prompt,
            category_hint=getattr(body, "category", None),
            style_hint=getattr(body, "visual_style", None),
            duration_hint=body.duration_seconds,
            reference_image_urls=ref_urls or None,
        )
        enhanced = plan.enhancement.enhanced_prompt
        t2v_summary: dict[str, Any] | None = None
        i2v_summary: dict[str, Any] | None = None
        avatar_summary: dict[str, Any] | None = None
        motion_summary: dict[str, Any] | None = None
        camera_motion_summary: dict[str, Any] | None = None
        physics_summary: dict[str, Any] | None = None
        motion_plan_obj: Any | None = None
        if enhanced and body.fields is not None:
            # Preserve original; feed enhanced + identity lock into generation.
            identity = " ".join(
                f"[{c.get('character_id')}] face/hair/outfit locked"
                for c in (plan.character_memory or [])
            )
            locked_prompt = f"{enhanced} {identity}".strip()
            if "mainPrompt" in body.fields or not body.fields.get("mainPrompt"):
                body.fields["mainPrompt"] = locked_prompt
            body.fields["rtasOriginalPrompt"] = raw_prompt
            body.fields["rtasIntelligencePlan"] = json.dumps(plan.to_dict())[:4000]
            if plan.production_package:
                body.fields["rtasProductionPackage"] = json.dumps(
                    plan.production_package
                )[:4000]
            if plan.master_ai_plan:
                body.fields["rtasMasterAiPlan"] = json.dumps(plan.master_ai_plan)[:4000]
            if plan.cinematic_quality:
                body.fields["rtasCinematicScore"] = str(
                    (plan.cinematic_quality or {}).get("overall", "")
                )
            if plan.prompt_understanding:
                body.fields["rtasPromptUnderstanding"] = json.dumps(
                    plan.prompt_understanding
                )[:4000]
            if plan.scene_breakdown:
                body.fields["rtasSceneBreakdown"] = json.dumps(
                    plan.scene_breakdown
                )[:4000]
            if plan.character_consistency:
                body.fields["rtasCharacterConsistency"] = json.dumps(
                    plan.character_consistency
                )[:4000]
            if plan.audio_director:
                body.fields["rtasAudioDirector"] = json.dumps(
                    plan.audio_director
                )[:4000]
            if plan.production_render:
                body.fields["rtasProductionRender"] = json.dumps(
                    {
                        "video_manifest": (plan.production_render or {}).get(
                            "video_manifest"
                        ),
                        "validation": (plan.production_render or {}).get("validation"),
                        "export_specs": (
                            (plan.production_render or {}).get("export_specs") or []
                        )[:6],
                    }
                )[:4000]
            # Phase 3 Sprint 1 — Real Text-to-Video Engine
            # Convert production package → scene/shot provider requests + queue.
            try:
                from app.services.text_to_video import (
                    build_and_register_from_intelligence,
                )

                t2v_job = build_and_register_from_intelligence(
                    production_package=plan.production_package,
                    scene_breakdown=plan.scene_breakdown,
                    character_memory=plan.character_memory,
                    director_plan=plan.director_plan,
                    production_render=plan.production_render,
                    visual_style=plan.visual_style,
                    parent_generation_id=generation_id,
                    enqueue=True,
                )
                t2v_summary = t2v_job.summary()
                body.fields["rtasTextToVideo"] = json.dumps(t2v_summary)[:4000]
                body.fields["rtasTextToVideoJobId"] = t2v_job.job_id
                # Prefer first shot prompt as generation seed when available
                if t2v_job.requests:
                    body.fields["rtasPrimaryShotPrompt"] = t2v_job.requests[0].prompt[
                        :2000
                    ]
            except Exception as t2v_exc:
                logger.warning("Text-to-video plan skipped: %s", t2v_exc)

            # Phase 3 Sprint 2 — Image-to-Video Engine (when images present).
            try:
                char_ref = None
                product_ref = None
                logo_ref = None
                multi_refs: list[str] = []
                for i, url in enumerate(ref_urls):
                    if i == 0:
                        char_ref = url
                    else:
                        multi_refs.append(url)
                # Prefer explicit face / product field names from files
                for key, meta in (files.items() if isinstance(files, dict) else []):
                    if isinstance(meta, dict):
                        url = meta.get("url") or meta.get("localPath") or meta.get("local_path")
                    else:
                        url = getattr(meta, "url", None) or getattr(meta, "local_path", None)
                    if not isinstance(url, str) or not url.strip():
                        continue
                    url = url.strip()
                    kl = str(key).lower()
                    if "face" in kl:
                        char_ref = url
                    elif "product" in kl:
                        product_ref = url
                    elif "logo" in kl:
                        logo_ref = url
                    elif "source" in kl or "reference" in kl or "cover" in kl:
                        if url not in multi_refs and url != char_ref:
                            multi_refs.append(url)

                if char_ref or product_ref or logo_ref or multi_refs or ref_urls:
                    from app.services.image_to_video import build_and_register

                    i2v_job = build_and_register(
                        prompt=locked_prompt if enhanced else raw_prompt,
                        single_image=ref_urls[0] if ref_urls and not char_ref else None,
                        multiple_images=multi_refs or None,
                        character_reference=char_ref,
                        product_reference=product_ref,
                        logo_reference=logo_ref,
                        production_package=plan.production_package,
                        scene_breakdown=plan.scene_breakdown,
                        character_memory=plan.character_memory,
                        director_plan=plan.director_plan,
                        parent_generation_id=generation_id,
                        enqueue=True,
                        preserve_identity=True,
                        preserve_lighting=True,
                        preserve_composition=True,
                        preserve_environment=True,
                    )
                    i2v_summary = i2v_job.summary()
                    body.fields["rtasImageToVideo"] = json.dumps(i2v_summary)[:4000]
                    body.fields["rtasImageToVideoJobId"] = i2v_job.job_id
                    if i2v_job.requests:
                        body.fields["rtasPrimaryI2VPrompt"] = i2v_job.requests[0].prompt[
                            :2000
                        ]
                        body.fields["rtasPrimaryI2VImage"] = i2v_job.requests[
                            0
                        ].primary_image_url[:500]
            except Exception as i2v_exc:
                logger.warning("Image-to-video plan skipped: %s", i2v_exc)

            # Phase 3 Sprint 3 — Talking Avatar Engine
            try:
                style = str(getattr(body, "visual_style", "") or "").lower()
                understanding = plan.prompt_understanding or {}
                scene_type = str(understanding.get("scene_type") or "").lower()
                wants_avatar = (
                    style == "avatar"
                    or "avatar" in scene_type
                    or "talking" in scene_type
                    or "presenter" in (raw_prompt or "").lower()
                    or bool(ref_urls)
                )
                if wants_avatar:
                    from app.services.talking_avatar import build_and_register

                    face_url = None
                    for key, meta in (files.items() if isinstance(files, dict) else []):
                        kl = str(key).lower()
                        if "face" not in kl:
                            continue
                        if isinstance(meta, dict):
                            face_url = meta.get("url") or meta.get("local_path")
                        else:
                            face_url = getattr(meta, "url", None) or getattr(
                                meta, "local_path", None
                            )
                        if isinstance(face_url, str) and face_url.strip():
                            face_url = face_url.strip()
                            break
                    if not face_url and ref_urls:
                        face_url = ref_urls[0]

                    avatar_job = build_and_register(
                        prompt=locked_prompt if enhanced else raw_prompt,
                        character_memory=plan.character_memory,
                        director_plan=plan.director_plan,
                        audio_director=plan.audio_director,
                        timeline=plan.timeline,
                        reference_face_url=face_url,
                        duration_hint=float(body.duration_seconds or 0) or None,
                        natural_motion=True,
                        parent_generation_id=generation_id,
                    )
                    avatar_summary = avatar_job.summary()
                    body.fields["rtasTalkingAvatar"] = json.dumps(avatar_summary)[:4000]
                    body.fields["rtasTalkingAvatarJobId"] = avatar_job.job_id
                    if avatar_job.provider_request:
                        body.fields["rtasAvatarPrompt"] = (
                            avatar_job.provider_request.prompt[:2000]
                        )
            except Exception as avatar_exc:
                logger.warning("Talking avatar plan skipped: %s", avatar_exc)

            # Phase 3 Sprint 4 — Professional Lip Sync Engine
            try:
                from app.services.lip_sync import build_lip_sync_plan

                dialogue_src = raw_prompt
                ad = plan.audio_director or {}
                for cue in ad.get("lip_sync_timeline") or []:
                    if isinstance(cue, dict) and cue.get("dialogue_snippet"):
                        dialogue_src = str(cue["dialogue_snippet"])
                        break
                ls_plan = build_lip_sync_plan(
                    dialogue_src,
                    language_hint=(ad.get("detection") or {}).get("language"),
                    emotion_hint=(ad.get("detection") or {}).get("emotion"),
                    duration_seconds=float(body.duration_seconds or 0) or None,
                    character_id=(
                        (plan.character_memory or [{}])[0].get("character_id")
                        if plan.character_memory
                        else None
                    ),
                    audio_director=ad,
                    voice_timeline=ad.get("voice_timeline"),
                )
                body.fields["rtasLipSync"] = json.dumps(ls_plan.summary())[:4000]
                body.fields["rtasLipSyncJobId"] = ls_plan.job_id
                body.fields["rtasLipSyncLanguage"] = ls_plan.language
            except Exception as ls_exc:
                logger.warning("Lip sync plan skipped: %s", ls_exc)

            # Phase 3 Sprint 5 — Motion Intelligence Engine
            try:
                from app.services.motion_intelligence import (
                    build_motion_intelligence_plan,
                )

                motion_plan = build_motion_intelligence_plan(
                    locked_prompt if enhanced else raw_prompt,
                    scenes=[s.to_dict() if hasattr(s, "to_dict") else s for s in (plan.scenes or [])],
                    cameras=[
                        c.to_dict() if hasattr(c, "to_dict") else c
                        for c in (plan.cameras or [])
                    ],
                    character_memory=plan.character_memory,
                    director_plan=plan.director_plan,
                    scene_breakdown=plan.scene_breakdown,
                    production_package=plan.production_package,
                    prompt_understanding=plan.prompt_understanding,
                    duration_seconds=float(body.duration_seconds or 0) or None,
                    parent_generation_id=generation_id,
                )
                motion_plan_obj = motion_plan
                motion_summary = motion_plan.summary()
                body.fields["rtasMotionIntelligence"] = json.dumps(motion_summary)[
                    :4000
                ]
                body.fields["rtasMotionJobId"] = motion_plan.job_id
                if motion_plan.scenes:
                    body.fields["rtasPrimaryLocomotion"] = (
                        motion_plan.scenes[0].primary_locomotion
                    )
            except Exception as motion_exc:
                logger.warning("Motion intelligence plan skipped: %s", motion_exc)

            # Phase 3 Sprint 6 — Camera Motion Engine
            try:
                from app.services.camera_motion import build_camera_motion_plan

                mi_payload: dict[str, Any] | None = motion_summary
                if motion_plan_obj is not None:
                    mi_payload = {
                        "job_id": motion_plan_obj.job_id,
                        "primary_locomotion": [
                            s.primary_locomotion for s in motion_plan_obj.scenes
                        ],
                        "scenes": [
                            {
                                "scene_index": s.scene_index,
                                "primary_locomotion": s.primary_locomotion,
                            }
                            for s in motion_plan_obj.scenes
                        ],
                    }

                cam_plan = build_camera_motion_plan(
                    locked_prompt if enhanced else raw_prompt,
                    scenes=[
                        s.to_dict() if hasattr(s, "to_dict") else s
                        for s in (plan.scenes or [])
                    ],
                    cameras=[
                        c.to_dict() if hasattr(c, "to_dict") else c
                        for c in (plan.cameras or [])
                    ],
                    shots=[
                        s.to_dict() if hasattr(s, "to_dict") else s
                        for s in (plan.shots or [])
                    ],
                    director_plan=plan.director_plan,
                    scene_breakdown=plan.scene_breakdown,
                    production_package=plan.production_package,
                    prompt_understanding=plan.prompt_understanding,
                    motion_intelligence=mi_payload,
                    duration_seconds=float(body.duration_seconds or 0) or None,
                    parent_generation_id=generation_id,
                )
                camera_motion_summary = cam_plan.summary()
                body.fields["rtasCameraMotion"] = json.dumps(camera_motion_summary)[
                    :4000
                ]
                body.fields["rtasCameraMotionJobId"] = cam_plan.job_id
                if cam_plan.scenes:
                    body.fields["rtasPrimaryCameraMotion"] = cam_plan.scenes[
                        0
                    ].primary_motion
            except Exception as cam_exc:
                logger.warning("Camera motion plan skipped: %s", cam_exc)

            # Phase 3 Sprint 7 — Physics Engine
            try:
                from app.services.physics import build_physics_plan

                phys_mi: dict[str, Any] | None = motion_summary
                if motion_plan_obj is not None:
                    phys_mi = {
                        "job_id": motion_plan_obj.job_id,
                        "primary_locomotion": [
                            s.primary_locomotion for s in motion_plan_obj.scenes
                        ],
                        "scenes": [
                            {
                                "scene_index": s.scene_index,
                                "primary_locomotion": s.primary_locomotion,
                            }
                            for s in motion_plan_obj.scenes
                        ],
                    }

                phys_plan = build_physics_plan(
                    locked_prompt if enhanced else raw_prompt,
                    scenes=[
                        s.to_dict() if hasattr(s, "to_dict") else s
                        for s in (plan.scenes or [])
                    ],
                    director_plan=plan.director_plan,
                    scene_breakdown=plan.scene_breakdown,
                    production_package=plan.production_package,
                    prompt_understanding=plan.prompt_understanding,
                    motion_intelligence=phys_mi,
                    character_memory=plan.character_memory,
                    duration_seconds=float(body.duration_seconds or 0) or None,
                    parent_generation_id=generation_id,
                )
                physics_summary = phys_plan.summary()
                body.fields["rtasPhysics"] = json.dumps(physics_summary)[:4000]
                body.fields["rtasPhysicsJobId"] = phys_plan.job_id
                if physics_summary.get("effects"):
                    body.fields["rtasPhysicsEffects"] = ",".join(
                        physics_summary["effects"][:12]
                    )
            except Exception as phys_exc:
                logger.warning("Physics plan skipped: %s", phys_exc)
        _structured(
            "intelligence_ready",
            generation_id=generation_id,
            user_id=user_id,
            scenes=len(plan.scenes),
            shots=len(plan.shots),
            characters=len(plan.character_memory or []),
            scene_type=(plan.prompt_understanding or {}).get("scene_type"),
            estimated_runtime=(
                ((plan.scene_breakdown or {}).get("Production") or {}).get(
                    "EstimatedRuntime"
                )
            ),
            consistency_score=(
                ((plan.character_consistency or {}).get("consistency_score") or {}).get(
                    "overall"
                )
            ),
            lip_sync_cues=len(
                (plan.audio_director or {}).get("lip_sync_timeline") or []
            ),
            export_validated=(
                ((plan.production_render or {}).get("validation") or {}).get("passed")
            ),
            t2v_requests=(t2v_summary or {}).get("requests") if t2v_summary else None,
            t2v_job_id=(t2v_summary or {}).get("job_id") if t2v_summary else None,
            i2v_requests=(i2v_summary or {}).get("requests") if i2v_summary else None,
            i2v_job_id=(i2v_summary or {}).get("job_id") if i2v_summary else None,
            avatar_lip_sync=(avatar_summary or {}).get("lip_sync_cues")
            if avatar_summary
            else None,
            avatar_job_id=(avatar_summary or {}).get("job_id") if avatar_summary else None,
            motion_scenes=(motion_summary or {}).get("scenes") if motion_summary else None,
            motion_job_id=(motion_summary or {}).get("job_id") if motion_summary else None,
            motion_primary=(
                ((motion_summary or {}).get("primary_locomotion") or [None])[0]
                if motion_summary
                else None
            ),
            camera_motion_scenes=(camera_motion_summary or {}).get("scenes")
            if camera_motion_summary
            else None,
            camera_motion_job_id=(camera_motion_summary or {}).get("job_id")
            if camera_motion_summary
            else None,
            camera_primary=(
                ((camera_motion_summary or {}).get("primary_motions") or [None])[0]
                if camera_motion_summary
                else None
            ),
            physics_effects=(physics_summary or {}).get("effects")
            if physics_summary
            else None,
            physics_job_id=(physics_summary or {}).get("job_id")
            if physics_summary
            else None,
            physics_particles=(physics_summary or {}).get("particle_systems")
            if physics_summary
            else None,
            cinematic_score=(plan.cinematic_quality or {}).get("overall"),
            quality_passed=plan.quality.passed,
        )
    except Exception as intel_exc:
        logger.warning("Intelligence pipeline skipped: %s", intel_exc)

    try:
        result = await run_generation(body)
    except LiveGenerationError as exc:
        _structured(
            "failed",
            generation_id=generation_id,
            user_id=user_id,
            provider=selected.name if selected else None,
            failure=str(exc),
            latency_ms=(time.perf_counter() - started) * 1000,
            error_code=getattr(exc, "error_code", None),
        )
        raise

    _structured(
        "success" if not result.simulation_mode else "simulation",
        generation_id=result.job_id,
        user_id=user_id,
        provider=result.provider,
        duration_seconds=result.duration_seconds,
        credits=result.credits_used,
        latency_ms=(time.perf_counter() - started) * 1000,
        simulation_mode=result.simulation_mode,
    )
    return result


async def provider_status(provider_name: str, external_job_id: str):
    adapters = get_provider_adapters()
    provider = adapters.get(provider_name)
    if not provider:
        raise LiveGenerationError(
            f"Unknown provider: {provider_name}",
            error_code="unknown_provider",
        )
    return await provider.status(external_job_id)


async def provider_cancel(provider_name: str, external_job_id: str) -> bool:
    adapters = get_provider_adapters()
    provider = adapters.get(provider_name)
    if not provider:
        return False
    return await provider.cancel(external_job_id)
