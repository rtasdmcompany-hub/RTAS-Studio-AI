import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import {
  classifyGenerationFailure,
  shouldRetryGenerationFailure,
} from "@rtas/shared";
import { authOptions } from "@/lib/auth/auth-options";
import { triggerAsyncGpuPipeline } from "@/lib/server/async-pipeline";
import {
  assertAndAcquireRenderingSlot,
  finalizeGenerationJobFailure,
  getGenerationJobForUser,
  retryGenerationJobForUser,
  updateGenerationJobPipeline,
} from "@/lib/server/studio-generation-guard";
import { getServerProfile } from "@/lib/server/profile-store";
import { profileToGenerateSnapshot } from "@/lib/server/tier-fal-routing";
import { logGeneration } from "@/lib/server/generation-logger";

export const runtime = "nodejs";

type RouteContext = { params: Promise<{ jobId: string }> | { jobId: string } };

async function resolveJobId(context: RouteContext): Promise<string> {
  const params = await Promise.resolve(context.params);
  return params.jobId;
}

/**
 * Retry a failed generation job (no UI). Re-queues GPU work from persisted settings.
 * Never double-charges credits.
 */
export async function POST(_request: Request, context: RouteContext) {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Authentication required" }, { status: 401 });
  }

  const jobId = await resolveJobId(context);
  const prior = await getGenerationJobForUser(jobId, session.user.id);
  if (!prior) {
    return NextResponse.json({ error: "not_found" }, { status: 404 });
  }

  const failureCode = classifyGenerationFailure(prior.errorMessage ?? "");
  if (
    prior.status === "FAILED" &&
    !shouldRetryGenerationFailure(failureCode, prior.retryCount ?? 0)
  ) {
    return NextResponse.json(
      { error: "not_retryable", code: failureCode },
      { status: 409 }
    );
  }

  const result = await retryGenerationJobForUser(jobId, session.user.id);
  if (!result.retried || !result.job) {
    const status =
      result.reason === "not_found"
        ? 404
        : result.reason === "max_retries" ||
            result.reason === "not_failed" ||
            result.reason === "already_charged"
          ? 409
          : 503;
    return NextResponse.json(
      { error: result.reason ?? "retry_failed" },
      { status }
    );
  }

  try {
    await assertAndAcquireRenderingSlot(session.user.id, {
      creditsRequired: Math.max(1, prior.creditsCharged || prior.durationSeconds || 1),
    });
  } catch (error) {
    await finalizeGenerationJobFailure(
      jobId,
      error instanceof Error ? error.message : "Unable to acquire render slot"
    );
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "slot_unavailable" },
      { status: 403 }
    );
  }

  const settings =
    prior.settings && typeof prior.settings === "object"
      ? (prior.settings as Record<string, unknown>)
      : {};
  const serverProfile = await getServerProfile(session.user.id);

  const proxyPayload: Record<string, unknown> = {
    ...settings,
    mode: settings.mode ?? "text",
    category: settings.category ?? "business",
    visualStyle: settings.visualStyle ?? "real",
    fields: settings.fields ?? { mainPrompt: prior.prompt ?? "" },
    files: settings.files ?? {},
    durationSeconds: prior.durationSeconds,
    userId: session.user.id,
    jobId,
    pipelineJobId: jobId,
    profile: profileToGenerateSnapshot(serverProfile),
  };

  const queued = await triggerAsyncGpuPipeline(proxyPayload, jobId);
  if (!queued.ok) {
    await finalizeGenerationJobFailure(
      jobId,
      queued.error ?? "Failed to re-queue GPU worker"
    );
    return NextResponse.json(
      { error: queued.error ?? "queue_failed" },
      { status: queued.status === 402 ? 402 : 503 }
    );
  }

  await updateGenerationJobPipeline({
    jobId,
    status: "generating",
    progressPercent: 15,
    stageLabel: "Retry — generating video",
  });

  logGeneration({
    event: "job_retry_dispatched",
    generationId: jobId,
    userId: session.user.id,
    retryCount: result.job.retryCount,
    status: "generating",
  });

  return NextResponse.json({
    ok: true,
    jobId,
    status: "queued",
    retryCount: result.job.retryCount,
    pollUrl: `/api/generate/jobs/${jobId}`,
  });
}
