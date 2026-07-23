import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth/auth-options";
import {
  checkRateLimitAsync,
  clientIpFromRequest,
  rateLimitResponse,
} from "@/lib/server/api-auth";
import { voteOnFeedback } from "@/lib/server/feedback-portal";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type Ctx = { params: Promise<{ id: string }> };

export async function POST(request: Request, context: Ctx) {
  const { id } = await context.params;
  if (!id || id.length > 80) {
    return NextResponse.json({ error: "Invalid feedback id." }, { status: 400 });
  }

  const ip = clientIpFromRequest(request) || "unknown";
  const limited = await checkRateLimitAsync(`feedback-vote:${ip}`, 60, 60 * 60_000);
  if (!limited.ok) return rateLimitResponse(limited.retryAfterSec);

  const session = await getServerSession(authOptions);
  const voterRaw = session?.user?.id
    ? `user:${session.user.id}`
    : `ip:${ip}`;

  const result = await voteOnFeedback(id, voterRaw);
  if (!result.ok) {
    const status = result.code === "DB_NOT_CONFIGURED" ? 503 : 400;
    return NextResponse.json(
      { error: result.error, code: result.code },
      { status }
    );
  }

  return NextResponse.json({
    ok: true,
    alreadyVoted: result.alreadyVoted,
    voteCount: result.voteCount,
  });
}
