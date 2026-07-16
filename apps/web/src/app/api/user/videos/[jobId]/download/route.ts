import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth/auth-options";
import { getGenerationJobForUser } from "@/lib/server/studio-generation-guard";

export const runtime = "nodejs";

type RouteContext = { params: Promise<{ jobId: string }> | { jobId: string } };

async function resolveJobId(context: RouteContext): Promise<string> {
  const params = await Promise.resolve(context.params);
  return params.jobId;
}

/**
 * Ownership-checked download helper for completed renders.
 * Returns the signed/public output URL — never exposes other users' jobs.
 */
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

  if (job.status !== "COMPLETED" || !job.generatedVideoUrl) {
    return NextResponse.json(
      { error: "Download available only for completed renders" },
      { status: 409 }
    );
  }

  return NextResponse.json({
    ok: true,
    jobId,
    downloadUrl: job.generatedVideoUrl,
    previewUrl: job.generatedVideoUrl,
    durationSeconds: job.durationSeconds,
    provider: job.provider,
  });
}
