/**
 * Central SaaS AI Generation Orchestrator (Next.js side).
 *
 * Validates → credits → job/project → provider proxy → progress → finalize.
 * Studio pages never talk to Fal/Replicate directly.
 */

import { NextResponse } from "next/server";
import { FREE_TRIAL_DURATION_SECONDS, computeSegmentPlan } from "@rtas/shared";
import { type GenerateBody } from "@/lib/generation";
import { proxyGenerateToFastApi } from "@/lib/server/fastapi-proxy";
import {
  shouldUseAsyncPipeline,
  triggerAsyncGpuPipeline,
} from "@/lib/server/async-pipeline";
import { isPrismaConfigured } from "@/lib/prisma";
import {
  buildGpuPipelineFailure,
  httpStatusForPipelineFailure,
} from "@/lib/server/gpu-pipeline-errors";
import {
  buildMockGenerationSuccess,
  GPU_UNAVAILABLE_MESSAGE,
  isMockGenerationAllowed,
  shouldFallbackToMockGeneration,
} from "@/lib/server/mock-generation";
import { clientIpFromRequest } from "@/lib/server/api-auth";
import { getServerProfile } from "@/lib/server/profile-store";
import {
  assertBillingForFalLive,
  profileToGenerateSnapshot,
} from "@/lib/server/tier-fal-routing";
import {
  FREE_TRIAL_ABUSE_MESSAGE,
  isFreeTrialBlocked,
} from "@/lib/server/trial-abuse-store";
import { logGeneration } from "@/lib/server/generation-logger";
import {
  assertAndAcquireRenderingSlot,
  completeGenerationJob,
  completeRenderingSlot,
  createGenerationJob,
  creditsRequiredForDuration,
  failGenerationJob,
  finalizeGenerationJobFailure,
  INSUFFICIENT_CREDITS_MESSAGE,
  MAX_CONCURRENT_TRACKS_MESSAGE,
  releaseRenderingSlotOnFailure,
  updateGenerationJobPipeline,
} from "@/lib/server/studio-generation-guard";

async function releaseSlotOnFailure(
  userId: string | null,
  skipBilling: boolean,
  previewOnly?: boolean,
  useFreeTrial?: boolean
) {
  if (!userId || skipBilling) return;
  await releaseRenderingSlotOnFailure(userId, { previewOnly, useFreeTrial });
}

export type OrchestrateGenerateInput = {
  userId: string;
  request: Request;
  body: GenerateBody & {
    jobId?: string;
    profile?: { subscriptionActive?: boolean; credits?: number };
    previewOnly?: boolean;
    useFreeTrial?: boolean;
    deviceFingerprint?: string;
  };
};

/**
 * Run one generation request through the full orchestrator pipeline.
 */
export async function orchestrateGeneration(
  input: OrchestrateGenerateInput
): Promise<NextResponse> {
  const { userId: effectiveUserId, request, body } = input;
  let jobId: string | null = null;
  let skipBilling = false;
  let previewOnly = false;
  let useFreeTrial = false;
  const startedAt = Date.now();

  try {
    const { mode, category, visualStyle, durationSeconds, fields, files } = body;

    const requestedPreview = Boolean(body.previewOnly);
    const requestedTrial = Boolean(body.useFreeTrial);

    const serverProfile = await getServerProfile(effectiveUserId);
    const accountTrialUsed =
      serverProfile.hasUsedFreeTrial ?? serverProfile.freeTrialUsed ?? false;

    useFreeTrial = false;
    previewOnly = false;

    if (requestedTrial) {
      const trialGate = await isFreeTrialBlocked({
        userId: effectiveUserId,
        ipAddress: clientIpFromRequest(request),
        deviceFingerprint: body.deviceFingerprint?.trim() ?? "",
        accountTrialUsed,
      });
      if (trialGate.blocked) {
        return NextResponse.json(
          { error: FREE_TRIAL_ABUSE_MESSAGE, reason: trialGate.reason },
          { status: 403 }
        );
      }
      useFreeTrial = true;
    } else if (requestedPreview) {
      const hasPaidCredits =
        serverProfile.subscriptionActive &&
        Number.isFinite(serverProfile.credits) &&
        serverProfile.credits > 0;
      if (hasPaidCredits) {
        return NextResponse.json(
          { error: "Preview mode is not available on an active paid plan." },
          { status: 400 }
        );
      }
      previewOnly = true;
    }

    skipBilling = previewOnly || useFreeTrial;

    if (!skipBilling) {
      const billingGate = assertBillingForFalLive(serverProfile, {
        previewOnly,
        useFreeTrial,
      });
      if (!billingGate.ok) {
        return NextResponse.json(
          { error: billingGate.message },
          { status: billingGate.status }
        );
      }
    }

    if (!mode || !category || !visualStyle || !durationSeconds) {
      return NextResponse.json({ error: "Missing required fields" }, { status: 400 });
    }

    if (visualStyle === "real") {
      const consent = fields?.faceConsent?.trim().toUpperCase();
      const hasFaceFile = Boolean(files?.faceReference);
      if (!hasFaceFile || consent !== "YES") {
        return NextResponse.json(
          {
            error:
              "Identity Preservation requires an identity reference photo and consent (YES) for content you own or are authorized to use",
          },
          { status: 400 }
        );
      }
    }

    const processedDurationSeconds = useFreeTrial
      ? Math.min(durationSeconds, FREE_TRIAL_DURATION_SECONDS)
      : durationSeconds;
    const creditsUsed = skipBilling
      ? 0
      : creditsRequiredForDuration(processedDurationSeconds);

    if (!skipBilling) {
      try {
        await assertAndAcquireRenderingSlot(effectiveUserId, {
          previewOnly,
          useFreeTrial,
          creditsRequired: creditsUsed,
        });
      } catch (error) {
        const message =
          error instanceof Error ? error.message : INSUFFICIENT_CREDITS_MESSAGE;
        const status =
          message === INSUFFICIENT_CREDITS_MESSAGE ||
          message === MAX_CONCURRENT_TRACKS_MESSAGE
            ? 403
            : 500;
        return NextResponse.json({ error: message }, { status });
      }
    }

    const promptPreview =
      fields?.directionPrompt?.trim() ||
      fields?.prompt?.trim() ||
      fields?.mainPrompt?.trim() ||
      null;
    const inputImageName =
      files?.sourceImage?.name ||
      files?.imageReference?.name ||
      files?.faceReference?.name ||
      null;
    const audioName = files?.audioSource?.name || files?.audio?.name || null;
    const backendJobId =
      typeof body.jobId === "string" && body.jobId.trim()
        ? body.jobId.trim()
        : null;
    const useAsyncPipeline =
      isPrismaConfigured() &&
      shouldUseAsyncPipeline({
        durationSeconds: processedDurationSeconds,
        previewOnly,
        useFreeTrial,
      });

    const settingsSnapshot = {
      mode,
      category,
      visualStyle,
      fields: fields ?? {},
      files: files ?? {},
      previewOnly,
      useFreeTrial,
    };

    // Always persist project/job history for billed + trial/preview when DB is up.
    if (isPrismaConfigured()) {
      const segmentPlan = computeSegmentPlan(processedDurationSeconds);
      const job = await createGenerationJob({
        userId: effectiveUserId,
        prompt: promptPreview,
        inputImageUrl: inputImageName ? `local://${inputImageName}` : null,
        audioUrl: audioName ? `local://${audioName}` : null,
        durationSeconds: processedDurationSeconds,
        creditsCharged: creditsUsed,
        chunkTotal: useAsyncPipeline ? segmentPlan.segmentCount : null,
        backendJobId,
        status: useAsyncPipeline ? "QUEUED" : "PREPARING",
        settings: settingsSnapshot,
        title: fields?.videoTitle?.trim() || promptPreview,
      });
      jobId = job?.id ?? null;
    }

    logGeneration({
      event: "orchestrator_start",
      generationId: jobId,
      userId: effectiveUserId,
      durationSeconds: processedDurationSeconds,
      credits: creditsUsed,
      status: useAsyncPipeline ? "queued" : "preparing",
    });

    const proxyPayload: Record<string, unknown> = {
      ...body,
      userId: effectiveUserId,
      durationSeconds: processedDurationSeconds,
      jobId: backendJobId ?? jobId ?? body.jobId,
      pipelineJobId: jobId ?? body.jobId,
      profile: profileToGenerateSnapshot(serverProfile),
    };

    if (useAsyncPipeline && jobId) {
      const queued = await triggerAsyncGpuPipeline(proxyPayload, jobId);
      if (!queued.ok) {
        await releaseSlotOnFailure(
          effectiveUserId,
          skipBilling,
          previewOnly,
          useFreeTrial
        );
        await finalizeGenerationJobFailure(
          jobId,
          queued.error ?? "Failed to queue GPU worker"
        );
        return NextResponse.json(
          { error: queued.error ?? "Failed to queue long render" },
          { status: queued.status === 402 ? 402 : 503 }
        );
      }

      await updateGenerationJobPipeline({
        jobId,
        status: "generating",
        chunkTotal: computeSegmentPlan(processedDurationSeconds).segmentCount,
        chunksCompleted: 0,
        progressPercent: 15,
        stageLabel: "Generating video",
      });

      return NextResponse.json(
        {
          status: "queued",
          pipelineStatus: "generating",
          jobId,
          projectId: jobId,
          pollUrl: `/api/generate/jobs/${jobId}`,
          message:
            "Long render queued — segments generate in parallel on the GPU worker",
          durationSeconds: processedDurationSeconds,
          creditsUsed,
          progressPercent: 15,
          stage: "generating",
        },
        { status: 202 }
      );
    }

    if (jobId) {
      await updateGenerationJobPipeline({
        jobId,
        status: "preparing",
        progressPercent: 12,
        stageLabel: "Preparing assets",
      });
    }

    let proxyResult: Awaited<ReturnType<typeof proxyGenerateToFastApi>>;
    try {
      if (jobId) {
        await updateGenerationJobPipeline({
          jobId,
          status: "generating",
          progressPercent: 40,
          stageLabel: "Generating video",
        });
      }
      proxyResult = await proxyGenerateToFastApi(proxyPayload);
    } catch (proxyError) {
      const details =
        proxyError instanceof Error
          ? proxyError.message
          : "Unexpected GPU proxy failure";
      await releaseSlotOnFailure(
        effectiveUserId,
        skipBilling,
        previewOnly,
        useFreeTrial
      );
      if (jobId) {
        await failGenerationJob(jobId, details);
      }

      if (!isMockGenerationAllowed() || !skipBilling) {
        logGeneration({
          event: "orchestrator_gpu_unavailable",
          generationId: jobId,
          userId: effectiveUserId,
          failure: details,
          latencyMs: Date.now() - startedAt,
        });
        return NextResponse.json(
          buildGpuPipelineFailure(503, GPU_UNAVAILABLE_MESSAGE, {
            timedOut: false,
          }),
          { status: 503 }
        );
      }

      const mock = buildMockGenerationSuccess({
        durationSeconds: processedDurationSeconds,
        promptPreview,
        category: String(category),
        jobId,
      });
      return NextResponse.json({
        ...mock,
        creditsUsed: 0,
        jobId: jobId ?? mock.jobId,
      });
    }

    if (!proxyResult.ok && shouldFallbackToMockGeneration(proxyResult) && skipBilling) {
      await releaseSlotOnFailure(
        effectiveUserId,
        skipBilling,
        previewOnly,
        useFreeTrial
      );
      const mock = buildMockGenerationSuccess({
        durationSeconds: processedDurationSeconds,
        promptPreview,
        category: String(category),
        jobId,
      });
      return NextResponse.json({
        ...mock,
        creditsUsed: 0,
        jobId: jobId ?? mock.jobId,
      });
    }

    if (!proxyResult.ok && !isMockGenerationAllowed()) {
      await releaseSlotOnFailure(
        effectiveUserId,
        skipBilling,
        previewOnly,
        useFreeTrial
      );
      if (jobId) {
        await failGenerationJob(
          jobId,
          typeof proxyResult.data.error === "string"
            ? proxyResult.data.error
            : GPU_UNAVAILABLE_MESSAGE
        );
      }
      return NextResponse.json(
        buildGpuPipelineFailure(503, GPU_UNAVAILABLE_MESSAGE, {
          timedOut: proxyResult.timedOut,
        }),
        { status: 503 }
      );
    }

    if (!proxyResult.ok) {
      await releaseSlotOnFailure(
        effectiveUserId,
        skipBilling,
        previewOnly,
        useFreeTrial
      );
      if (jobId) {
        await failGenerationJob(
          jobId,
          typeof proxyResult.data.error === "string"
            ? proxyResult.data.error
            : "Generation failed"
        );
      }

      const errorMessage =
        typeof proxyResult.data.error === "string"
          ? proxyResult.data.error
          : "Generation failed";

      const failure = buildGpuPipelineFailure(proxyResult.status, errorMessage, {
        timedOut: proxyResult.timedOut,
      });

      logGeneration({
        event: "orchestrator_provider_failed",
        generationId: jobId,
        userId: effectiveUserId,
        failure: errorMessage,
        latencyMs: Date.now() - startedAt,
      });

      return NextResponse.json(failure, {
        status: httpStatusForPipelineFailure(failure, proxyResult.status),
      });
    }

    const videoUrl = String(
      proxyResult.data.videoUrl ?? proxyResult.data.video_url ?? ""
    );
    const simulationMode = Boolean(
      proxyResult.data.simulationMode ?? proxyResult.data.simulation_mode
    );
    const provider = String(
      proxyResult.data.provider ?? proxyResult.data.uiProvider ?? "fal"
    );

    if (!skipBilling && simulationMode) {
      await releaseSlotOnFailure(
        effectiveUserId,
        skipBilling,
        previewOnly,
        useFreeTrial
      );
      if (jobId) {
        await failGenerationJob(
          jobId,
          "Live AI provider returned a simulation result for a paid render"
        );
      }
      return NextResponse.json(
        buildGpuPipelineFailure(
          503,
          "Live AI generation required for paid renders. Configure FAL_KEY or Replicate on the GPU worker."
        ),
        { status: 503 }
      );
    }

    if (jobId) {
      await updateGenerationJobPipeline({
        jobId,
        status: "uploading",
        progressPercent: 96,
        stageLabel: "Uploading output",
        provider,
      });
    }

    // Debit credits first, then mark the job — never double-charge on retries.
    if (!skipBilling) {
      await completeRenderingSlot(effectiveUserId, {
        previewOnly,
        useFreeTrial,
        creditsToDebit: creditsUsed,
      });
    }

    if (jobId && videoUrl) {
      await completeGenerationJob(jobId, videoUrl, {
        markCreditsDebited: !skipBilling,
        provider,
      });
    }

    logGeneration({
      event: "orchestrator_success",
      generationId: jobId,
      userId: effectiveUserId,
      provider,
      credits: creditsUsed,
      durationSeconds: processedDurationSeconds,
      latencyMs: Date.now() - startedAt,
      status: "completed",
    });

    return NextResponse.json({
      status: "success",
      ...proxyResult.data,
      creditsUsed,
      provider,
      jobId: jobId ?? proxyResult.data.jobId ?? proxyResult.data.job_id,
      progressPercent: 100,
      stage: "completed",
    });
  } catch (e) {
    await releaseSlotOnFailure(
      effectiveUserId,
      skipBilling,
      previewOnly,
      useFreeTrial
    );
    if (jobId) {
      await failGenerationJob(jobId);
    }

    const details = e instanceof Error ? e.message : "Generation failed";
    const failure = buildGpuPipelineFailure(500, details);

    logGeneration({
      event: "orchestrator_unhandled",
      generationId: jobId,
      userId: effectiveUserId,
      failure: details,
      latencyMs: Date.now() - startedAt,
    });

    return NextResponse.json(failure, {
      status: httpStatusForPipelineFailure(failure, 500),
    });
  }
}
