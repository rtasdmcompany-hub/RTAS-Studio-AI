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
import {
  requireApiSession,
  checkRateLimitAsync,
  rateLimitResponse,
  clientIpFromRequest,
} from "@/lib/server/api-auth";
import { getServerProfile } from "@/lib/server/profile-store";
import {
  assertBillingForFalLive,
  profileToGenerateSnapshot,
} from "@/lib/server/tier-fal-routing";
import {
  FREE_TRIAL_ABUSE_MESSAGE,
  isFreeTrialBlocked,
} from "@/lib/server/trial-abuse-store";
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

export const runtime = "nodejs";
export const maxDuration = 300;

const AUTH_REQUIRED_BODY = {
  error: "Authentication required. Please log in to access the studio.",
} as const;

async function releaseSlotOnFailure(
  userId: string | null,
  skipBilling: boolean,
  previewOnly?: boolean,
  useFreeTrial?: boolean
) {
  if (!userId || skipBilling) return;
  await releaseRenderingSlotOnFailure(userId, { previewOnly, useFreeTrial });
}

/**
 * Credit-guarded generation gateway. All studio renders proxy to FastAPI
 * server-side so clients cannot bypass SaaS billing controls.
 */
export async function POST(request: Request) {
  const auth = await requireApiSession();
  if (!auth.ok) {
    return NextResponse.json(AUTH_REQUIRED_BODY, { status: auth.response.status });
  }

  const ip = clientIpFromRequest(request) || "unknown";
  const limited = await checkRateLimitAsync(
    `generate:${auth.userId}:${ip}`,
    30,
    60_000
  );
  if (!limited.ok) return rateLimitResponse(limited.retryAfterSec);

  const effectiveUserId = auth.userId;
  let jobId: string | null = null;
  let skipBilling = false;
  let previewOnly = false;
  let useFreeTrial = false;

  try {
    const body = (await request.json()) as GenerateBody & {
      jobId?: string;
      profile?: { subscriptionActive?: boolean; credits?: number };
      previewOnly?: boolean;
      useFreeTrial?: boolean;
      deviceFingerprint?: string;
    };

    const { mode, category, visualStyle, durationSeconds, fields, files } = body;

    const requestedPreview = Boolean(body.previewOnly);
    const requestedTrial = Boolean(body.useFreeTrial);

    const serverProfile = await getServerProfile(effectiveUserId);
    const accountTrialUsed =
      serverProfile.hasUsedFreeTrial ?? serverProfile.freeTrialUsed ?? false;

    // Never trust client billing flags — re-validate trial/preview server-side.
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
      // Preview skip is only for unpaid / zero-credit accounts (not a paid bypass).
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
      await releaseSlotOnFailure(
        effectiveUserId,
        skipBilling,
        previewOnly,
        useFreeTrial
      );
      return NextResponse.json({ error: "Missing required fields" }, { status: 400 });
    }

    if (visualStyle === "real") {
      const consent = fields?.faceConsent?.trim().toUpperCase();
      const hasFaceFile = Boolean(files?.faceReference);
      if (!hasFaceFile || consent !== "YES") {
        await releaseSlotOnFailure(
          effectiveUserId,
          skipBilling,
          previewOnly,
          useFreeTrial
        );
        return NextResponse.json(
          { error: "Real face mode requires Face Photo upload and consent (YES)" },
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

    if (!skipBilling) {
      const segmentPlan = computeSegmentPlan(processedDurationSeconds);
      const job = await createGenerationJob({
        userId: effectiveUserId,
        prompt: promptPreview,
        inputImageUrl: inputImageName ? `local://${inputImageName}` : null,
        durationSeconds: processedDurationSeconds,
        creditsCharged: creditsUsed,
        chunkTotal: useAsyncPipeline ? segmentPlan.segmentCount : null,
        backendJobId,
        status: useAsyncPipeline ? "QUEUED" : "GENERATING_CHUNKS",
      });
      jobId = job?.id ?? null;
    }

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
        status: "generating_chunks",
        chunkTotal: computeSegmentPlan(processedDurationSeconds).segmentCount,
        chunksCompleted: 0,
      });

      return NextResponse.json(
        {
          status: "queued",
          pipelineStatus: "generating_chunks",
          jobId,
          pollUrl: `/api/generate/jobs/${jobId}`,
          message:
            "Long render queued — segments generate in parallel on the GPU worker",
          durationSeconds: processedDurationSeconds,
          creditsUsed,
        },
        { status: 202 }
      );
    }

    let proxyResult: Awaited<ReturnType<typeof proxyGenerateToFastApi>>;
    try {
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
        console.error("[generate] GPU proxy exception — hard fail:", details);
        return NextResponse.json(
          buildGpuPipelineFailure(503, GPU_UNAVAILABLE_MESSAGE, {
            timedOut: false,
          }),
          { status: 503 }
        );
      }

      console.warn("[generate] GPU proxy exception — using mock preview:", details);
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
      const errorMessage =
        typeof proxyResult.data.error === "string"
          ? proxyResult.data.error
          : "GPU worker unavailable";
      console.warn(
        `[generate] GPU unavailable (${proxyResult.status}) — mock preview:`,
        errorMessage
      );

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
        await failGenerationJob(jobId);
      }

      const errorMessage =
        typeof proxyResult.data.error === "string"
          ? proxyResult.data.error
          : "Generation failed";

      const failure = buildGpuPipelineFailure(
        proxyResult.status,
        errorMessage,
        { timedOut: proxyResult.timedOut }
      );

      console.error(
        `[generate] GPU pipeline failed (${failure.code ?? "unknown"}):`,
        errorMessage
      );

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

    // Paid renders must never accept a simulation/showcase success from the worker.
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

    if (jobId && videoUrl) {
      await completeGenerationJob(jobId, videoUrl);
    }

    if (!skipBilling) {
      await completeRenderingSlot(effectiveUserId, {
        previewOnly,
        useFreeTrial,
        creditsToDebit: creditsUsed,
      });
    }

    return NextResponse.json({
      status: "success",
      ...proxyResult.data,
      creditsUsed,
      jobId: jobId ?? proxyResult.data.jobId ?? proxyResult.data.job_id,
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

    console.error("[generate] Unhandled generation error:", details);

    return NextResponse.json(failure, {
      status: httpStatusForPipelineFailure(failure, 500),
    });
  }
}
