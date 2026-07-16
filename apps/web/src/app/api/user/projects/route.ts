import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth/auth-options";
import { listProjectsForUser } from "@/lib/server/studio-generation-guard";

export const runtime = "nodejs";

/** List the authenticated user's generation projects (history). */
export async function GET(request: Request) {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Authentication required" }, { status: 401 });
  }

  const { searchParams } = new URL(request.url);
  const limit = Number(searchParams.get("limit") ?? 24);
  const projects = await listProjectsForUser(session.user.id, limit);

  return NextResponse.json({
    ok: true,
    items: projects.map((p) => ({
      id: p.id,
      title: p.title,
      prompt: p.prompt,
      outputUrl: p.outputUrl,
      status: p.status,
      durationSeconds: p.durationSeconds,
      creditsUsed: p.creditsUsed,
      provider: p.provider,
      latestJobId: p.latestJobId,
      createdAt: p.createdAt.toISOString(),
      actions: {
        preview: Boolean(p.outputUrl),
        download: Boolean(p.outputUrl && p.status === "completed"),
        share: Boolean(p.outputUrl && p.status === "completed"),
        duplicate: true,
        generateAgain: true,
      },
    })),
  });
}
