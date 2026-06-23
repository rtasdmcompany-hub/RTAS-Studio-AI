import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { FREE_TRIAL_DURATION_SECONDS } from "@rtas/shared";
import { type GenerateBody } from "@/lib/generation";
import { authOptions } from "@/lib/auth/auth-options";
import { proxyGenerateToFastApi } from "@/lib/server/fastapi-proxy";
import {
  buildGpuPipelineFailure,
  httpStatusForPipelineFailure,
} from "@/lib/server/gpu-pipeline-errors";
import {
  assertAndAcquireRenderingSlot,
  completeGenerationJob,
  completeRenderingSlot,
  createGenerationJob,
  CREDITS_PER_RENDER,
  failGenerationJob,
  INSUFFICIENT_CREDITS_MESSAGE,
  MAX_CONCURRENT_TRACKS_MESSAGE,
  releaseRenderingSlotOnFailure,
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
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json(AUTH_REQUIRED_BODY, { status: 401 });
  }

  const effectiveUserId = session.user.id;
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

    previewOnly = Boolean(body.previewOnly);
    useFreeTrial = Boolean(body.useFreeTrial);
    skipBilling = previewOnly || useFreeTrial;

    if (!skipBilling) {
      try {
        await assertAndAcquireRenderingSlot(effectiveUserId, {
          previewOnly,
          useFreeTrial,
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

    const promptPreview =
      fields?.directionPrompt?.trim() ||
      fields?.prompt?.trim() ||
      fields?.mainPrompt?.trim() ||
      null;
    const inputImageName =
      files?.sourceImage?.name || files?.imageReference?.name || null;
    const creditsUsed = skipBilling ? 0 : CREDITS_PER_RENDER;

    if (!skipBilling) {
      const job = await createGenerationJob({
        userId: effectiveUserId,
        prompt: promptPreview,
        inputImageUrl: inputImageName ? `local://${inputImageName}` : null,
        durationSeconds: processedDurationSeconds,
        creditsCharged: creditsUsed,
      });
      jobId = job?.id ?? null;
    }

    const proxyPayload: Record<string, unknown> = {
      ...body,
      userId: effectiveUserId,
      durationSeconds: processedDurationSeconds,
    };

    let proxyResult: Awaited<ReturnType<typeof proxyGenerateToFastApi>>;
    try {
      proxyResult = await proxyGenerateToFastApi(proxyPayload);
    } catch (proxyError) {
      await releaseSlotOnFailure(
        effectiveUserId,
        skipBilling,
        previewOnly,
        useFreeTrial
      );
      if (jobId) {
        await failGenerationJob(jobId);
      }

      const details =
        proxyError instanceof Error
          ? proxyError.message
          : "Unexpected GPU proxy failure";
      const failure = buildGpuPipelineFailure(503, details);

      console.error("[generate] GPU proxy exception:", details);

      return NextResponse.json(failure, {
        status: httpStatusForPipelineFailure(failure, 503),
      });
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

    if (jobId && videoUrl) {
      await completeGenerationJob(jobId, videoUrl);
    }

    if (!skipBilling) {
      await completeRenderingSlot(effectiveUserId, { previewOnly, useFreeTrial });
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
