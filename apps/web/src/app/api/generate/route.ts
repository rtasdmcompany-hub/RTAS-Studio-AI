import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { FREE_TRIAL_DURATION_SECONDS } from "@rtas/shared";
import { type GenerateBody } from "@/lib/generation";
import { authOptions } from "@/lib/auth/auth-options";
import { proxyGenerateToFastApi } from "@/lib/server/fastapi-proxy";
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

/**
 * Credit-guarded generation gateway. All studio renders proxy to FastAPI
 * server-side so clients cannot bypass SaaS billing controls.
 */
export async function POST(request: Request) {
  let jobId: string | null = null;
  let effectiveUserId: string | null = null;
  let skipBilling = false;

  try {
    const session = await getServerSession(authOptions);
    const body = (await request.json()) as GenerateBody & {
      userId?: string;
      jobId?: string;
      profile?: { subscriptionActive?: boolean; credits?: number };
      previewOnly?: boolean;
      useFreeTrial?: boolean;
      deviceFingerprint?: string;
    };

    const {
      userId,
      mode,
      category,
      visualStyle,
      durationSeconds,
      fields,
      files,
      previewOnly,
      useFreeTrial,
    } = body;

    const sessionUserId = session?.user?.id;
    effectiveUserId = sessionUserId ?? userId ?? null;
    skipBilling = Boolean(previewOnly || useFreeTrial);

    if (effectiveUserId && !skipBilling) {
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
      if (effectiveUserId && !skipBilling) {
        await releaseRenderingSlotOnFailure(effectiveUserId, {
          previewOnly,
          useFreeTrial,
        });
      }
      return NextResponse.json({ error: "Missing required fields" }, { status: 400 });
    }

    if (visualStyle === "real") {
      const consent = fields?.faceConsent?.trim().toUpperCase();
      const hasFaceFile = Boolean(files?.faceReference);
      if (!hasFaceFile || consent !== "YES") {
        if (effectiveUserId && !skipBilling) {
          await releaseRenderingSlotOnFailure(effectiveUserId, {
            previewOnly,
            useFreeTrial,
          });
        }
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

    if (effectiveUserId && !skipBilling) {
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
      userId: effectiveUserId ?? body.userId,
      durationSeconds: processedDurationSeconds,
    };

    const proxyResult = await proxyGenerateToFastApi(proxyPayload);

    if (!proxyResult.ok) {
      if (effectiveUserId && !skipBilling) {
        await releaseRenderingSlotOnFailure(effectiveUserId, {
          previewOnly,
          useFreeTrial,
        });
      }
      if (jobId) {
        await failGenerationJob(jobId);
      }

      const errorMessage =
        typeof proxyResult.data.error === "string"
          ? proxyResult.data.error
          : "Generation failed";

      return NextResponse.json(
        { error: errorMessage, ...proxyResult.data },
        { status: proxyResult.status }
      );
    }

    const videoUrl = String(
      proxyResult.data.videoUrl ?? proxyResult.data.video_url ?? ""
    );

    if (jobId && videoUrl) {
      await completeGenerationJob(jobId, videoUrl);
    }

    if (effectiveUserId && !skipBilling) {
      await completeRenderingSlot(effectiveUserId, { previewOnly, useFreeTrial });
    }

    return NextResponse.json({
      ...proxyResult.data,
      creditsUsed,
      jobId: jobId ?? proxyResult.data.jobId ?? proxyResult.data.job_id,
    });
  } catch (e) {
    if (effectiveUserId && !skipBilling) {
      await releaseRenderingSlotOnFailure(effectiveUserId);
    }
    if (jobId) {
      await failGenerationJob(jobId);
    }
    const message = e instanceof Error ? e.message : "Generation failed";
    console.error("Generation error:", message);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
