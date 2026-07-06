import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { pipelineStatusLabel, type PipelineStatus } from "@rtas/shared";
import { authOptions } from "@/lib/auth/auth-options";
import {
  finalizeGenerationJobFailure,
  finalizeGenerationJobSuccess,
  getGenerationJobForUser,
  updateGenerationJobPipeline,
} from "@/lib/server/studio-generation-guard";
import { verifyGenerationWebhook } from "@/lib/server/generation-webhook";

function prismaToPipelineStatus(status: string): PipelineStatus {
  switch (status.toUpperCase()) {
    case "QUEUED":
      return "queued";
    case "GENERATING_CHUNKS":
      return "generating_chunks";
    case "COMPILING_MEDIA":
      return "compiling_media";
    case "COMPLETED":
      return "completed";
    case "FAILED":
      return "failed";
    default:
      return "queued";
  }
}

function serializeJob(job: NonNullable<Awaited<ReturnType<typeof getGenerationJobForUser>>>) {
  const pipelineStatus = prismaToPipelineStatus(job.status);
  return {
    id: job.id,
    status: pipelineStatus,
    pipelineStatus,
    statusLabel: pipelineStatusLabel(pipelineStatus),
    prompt: job.prompt,
    generatedVideoUrl: job.generatedVideoUrl,
    durationSeconds: job.durationSeconds,
    creditsCharged: job.creditsCharged,
    chunkTotal: job.chunkTotal,
    chunksCompleted: job.chunksCompleted,
    chunkManifest: job.chunkManifest,
    errorMessage: job.errorMessage,
    backendJobId: job.backendJobId,
    createdAt: job.createdAt,
    completedAt: job.completedAt,
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

/** GPU worker webhook — updates Supabase/Postgres pipeline grid. */
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
  };

  if (!body.status) {
    return NextResponse.json({ error: "status is required" }, { status: 400 });
  }

  const pipelineStatus = body.status.toLowerCase();

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

  await updateGenerationJobPipeline({
    jobId,
    status: pipelineStatus,
    chunksCompleted: body.chunksCompleted,
    chunkTotal: body.chunkTotal,
    chunkManifest: body.chunkManifest,
    errorMessage: body.errorMessage,
    backendJobId: body.backendJobId,
  });

  return NextResponse.json({ ok: true, id: jobId, status: pipelineStatus });
}
