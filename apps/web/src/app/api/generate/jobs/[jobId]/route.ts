import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import {
  computeJobProgress,
  normalizeJobLifecycleStatus,
  pipelineStatusLabel,
  type PipelineStatus,
} from "@rtas/shared";
import { authOptions } from "@/lib/auth/auth-options";
import {
  finalizeGenerationJobFailure,
  finalizeGenerationJobSuccess,
  getGenerationJobForUser,
  updateGenerationJobPipeline,
} from "@/lib/server/studio-generation-guard";
import { verifyGenerationWebhook } from "@/lib/server/generation-webhook";
import { logGeneration } from "@/lib/server/generation-logger";

function prismaToPipelineStatus(status: string): PipelineStatus {
  return normalizeJobLifecycleStatus(status) as PipelineStatus;
}

function serializeJob(
  job: NonNullable<Awaited<ReturnType<typeof getGenerationJobForUser>>>
) {
  const pipelineStatus = prismaToPipelineStatus(job.status);
  const progress = computeJobProgress({
    status: job.status,
    progressPercent: job.progressPercent,
    chunkTotal: job.chunkTotal,
    chunksCompleted: job.chunksCompleted,
    durationSeconds: job.durationSeconds,
    startedAt: job.startedAt,
  });

  return {
    id: job.id,
    status: pipelineStatus,
    pipelineStatus,
    statusLabel: job.stageLabel || pipelineStatusLabel(pipelineStatus),
    stage: progress.stage,
    stageLabel: progress.stageLabel,
    progressPercent: progress.percent,
    queuePosition: job.queuePosition ?? null,
    estimatedSecondsRemaining:
      job.estimatedSecondsRemaining ?? progress.estimatedSecondsRemaining,
    prompt: job.prompt,
    generatedVideoUrl: job.generatedVideoUrl,
    durationSeconds: job.durationSeconds,
    creditsCharged: job.creditsCharged,
    creditsDebited: job.creditsDebited,
    provider: job.provider,
    projectId: job.projectId,
    chunkTotal: job.chunkTotal,
    chunksCompleted: job.chunksCompleted,
    chunkManifest: job.chunkManifest,
    errorMessage: job.errorMessage,
    backendJobId: job.backendJobId,
    retryCount: job.retryCount,
    settings: job.settings,
    inputImageUrl: job.inputImageUrl,
    audioUrl: job.audioUrl,
    createdAt: job.createdAt,
    startedAt: job.startedAt,
    completedAt: job.completedAt,
    cancelledAt: job.cancelledAt,
    // Download / preview / share helpers (ownership already verified)
    actions: {
      preview: Boolean(job.generatedVideoUrl),
      download: Boolean(job.generatedVideoUrl && pipelineStatus === "completed"),
      share: pipelineStatus === "completed",
      duplicate: true,
      generateAgain: true,
      cancel: !["completed", "failed", "cancelled"].includes(pipelineStatus),
    },
  };
}

type RouteContext = { params: Promise<{ jobId: string }> | { jobId: string } };

async function resolveJobId(context: RouteContext): Promise<string> {
  const params = await Promise.resolve(context.params);
  return params.jobId;
}

/** Poll long-render pipeline state for the authenticated studio user. */
export async function GET(_request: Request, context: RouteContext) {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Authentication required" }, { status: 401 });
  }

  const jobId = await resolveJobId(context);
  const job = await getGenerationJobForUser(jobId, session.user.id);
  if (!job) {
    return NextResponse.json({ error: "Job not found" }, { status: 404 });
  }

  return NextResponse.json(serializeJob(job));
}

/** GPU worker webhook — updates Postgres pipeline grid. */
export async function PATCH(request: Request, context: RouteContext) {
  if (!verifyGenerationWebhook(request)) {
    return NextResponse.json({ error: "Unauthorized webhook" }, { status: 401 });
  }

  const jobId = await resolveJobId(context);
  const body = (await request.json()) as {
    status?: string;
    chunksCompleted?: number;
    chunkTotal?: number;
    chunkManifest?: unknown;
    generatedVideoUrl?: string;
    errorMessage?: string;
    backendJobId?: string;
    provider?: string;
    progressPercent?: number;
    stageLabel?: string;
    queuePosition?: number | null;
    estimatedSecondsRemaining?: number | null;
  };

  if (!body.status) {
    return NextResponse.json({ error: "status is required" }, { status: 400 });
  }

  const pipelineStatus = body.status.toLowerCase();

  logGeneration({
    event: "webhook_status",
    generationId: jobId,
    status: pipelineStatus,
    provider: body.provider ?? null,
  });

  if (pipelineStatus === "completed" && body.generatedVideoUrl) {
    await finalizeGenerationJobSuccess(jobId, body.generatedVideoUrl);
    return NextResponse.json({
      ok: true,
      id: jobId,
      status: "completed",
      generatedVideoUrl: body.generatedVideoUrl,
    });
  }

  if (pipelineStatus === "failed") {
    await finalizeGenerationJobFailure(jobId, body.errorMessage);
    return NextResponse.json({ ok: true, id: jobId, status: "failed" });
  }

  if (pipelineStatus === "cancelled" || pipelineStatus === "canceled") {
    await finalizeGenerationJobFailure(jobId, body.errorMessage ?? "Cancelled");
    return NextResponse.json({ ok: true, id: jobId, status: "cancelled" });
  }

  await updateGenerationJobPipeline({
    jobId,
    status: pipelineStatus,
    chunksCompleted: body.chunksCompleted,
    chunkTotal: body.chunkTotal,
    chunkManifest: body.chunkManifest,
    errorMessage: body.errorMessage,
    backendJobId: body.backendJobId,
    provider: body.provider,
    progressPercent: body.progressPercent,
    stageLabel: body.stageLabel,
    queuePosition: body.queuePosition,
    estimatedSecondsRemaining: body.estimatedSecondsRemaining,
  });

  return NextResponse.json({ ok: true, id: jobId, status: pipelineStatus });
}
