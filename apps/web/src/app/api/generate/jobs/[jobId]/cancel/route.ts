import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth/auth-options";
import { cancelGenerationJobForUser } from "@/lib/server/studio-generation-guard";

export const runtime = "nodejs";

type RouteContext = { params: Promise<{ jobId: string }> | { jobId: string } };

async function resolveJobId(context: RouteContext): Promise<string> {
  const params = await Promise.resolve(context.params);
  return params.jobId;
}

/** Cancel an in-flight generation. Never charges credits. */
export async function POST(_request: Request, context: RouteContext) {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Authentication required" }, { status: 401 });
  }

  const jobId = await resolveJobId(context);
  const result = await cancelGenerationJobForUser(jobId, session.user.id);

  if (!result.cancelled) {
    const status =
      result.reason === "not_found"
        ? 404
        : result.reason === "already_terminal"
          ? 409
          : 503;
    return NextResponse.json(
      { error: result.reason ?? "cancel_failed" },
      { status }
    );
  }

  return NextResponse.json({ ok: true, id: jobId, status: "cancelled" });
}
