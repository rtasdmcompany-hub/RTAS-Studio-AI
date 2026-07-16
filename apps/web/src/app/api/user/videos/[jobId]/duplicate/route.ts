import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth/auth-options";
import { duplicateProjectForUser } from "@/lib/server/studio-generation-guard";

export const runtime = "nodejs";

type RouteContext = { params: Promise<{ jobId: string }> | { jobId: string } };

async function resolveJobId(context: RouteContext): Promise<string> {
  const params = await Promise.resolve(context.params);
  return params.jobId;
}

/** Duplicate a completed/previous job into a new Project for Generate Again. */
export async function POST(_request: Request, context: RouteContext) {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Authentication required" }, { status: 401 });
  }

  const jobId = await resolveJobId(context);
  const result = await duplicateProjectForUser(jobId, session.user.id);

  if (!result.ok || !result.project) {
    const status = result.reason === "not_found" ? 404 : 503;
    return NextResponse.json(
      { error: result.reason ?? "duplicate_failed" },
      { status }
    );
  }

  return NextResponse.json({
    ok: true,
    project: result.project,
    message: "Project duplicated — reopen settings and Generate Again.",
  });
}
