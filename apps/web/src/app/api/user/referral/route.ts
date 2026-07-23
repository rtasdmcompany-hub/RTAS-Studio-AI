import { NextResponse } from "next/server";
import {
  checkRateLimitAsync,
  rateLimitResponse,
  requireApiSession,
} from "@/lib/server/api-auth";
import {
  getOrCreateReferralForUser,
  inviteReferral,
} from "@/lib/marketing/referral";

export const runtime = "nodejs";

export async function GET() {
  const auth = await requireApiSession();
  if (!auth.ok) return auth.response;

  const summary = await getOrCreateReferralForUser(auth.userId);
  return NextResponse.json({ ok: true, referral: summary });
}

export async function POST(request: Request) {
  const auth = await requireApiSession();
  if (!auth.ok) return auth.response;

  const limited = await checkRateLimitAsync(
    `referral-invite:${auth.userId}`,
    10,
    60 * 60_000
  );
  if (!limited.ok) return rateLimitResponse(limited.retryAfterSec);

  let body: { email?: string } = {};
  try {
    body = (await request.json()) as { email?: string };
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  const result = await inviteReferral({
    referrerUserId: auth.userId,
    email: body.email ?? "",
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 400 });
  }

  const summary = await getOrCreateReferralForUser(auth.userId);
  return NextResponse.json({
    ok: true,
    referralId: result.referralId,
    referral: summary,
    note: "Proposed — invite recorded; reward credits are not auto-granted yet.",
  });
}
