import { NextResponse } from "next/server";
import { getPublicShare, publishPublicShare } from "@/lib/server/share-store";
import {
  checkRateLimitAsync,
  clientIpFromRequest,
  rateLimitResponse,
  requireApiSession,
} from "@/lib/server/api-auth";

export const runtime = "nodejs";

type RouteContext = { params: { videoId: string } };

type PublishBody = {
  title?: string;
  prompt?: string | null;
  videoUrl?: string;
  durationSeconds?: number;
  category?: string;
  visualStyle?: string;
  mode?: string;
};

function isAllowedShareVideoUrl(videoUrl: string): boolean {
  const appUrl = (process.env.NEXT_PUBLIC_APP_URL ?? "").replace(/\/$/, "");
  const fastApi = (process.env.FASTAPI_URL ?? "").replace(/\/$/, "");

  if (videoUrl.startsWith("/")) return true;
  if (appUrl && (videoUrl === appUrl || videoUrl.startsWith(`${appUrl}/`))) {
    return true;
  }
  if (fastApi && videoUrl.startsWith(`${fastApi}/`)) return true;

  // Known media path patterns on same deployment host
  try {
    const u = new URL(videoUrl);
    if (u.protocol !== "https:" && u.protocol !== "http:") return false;
    if (appUrl) {
      const appHost = new URL(appUrl).host;
      if (u.host === appHost) return true;
    }
  } catch {
    return false;
  }
  return false;
}

/** Public read — no session required */
export async function GET(_request: Request, context: RouteContext) {
  const videoId = context.params.videoId?.trim();
  if (!videoId) {
    return NextResponse.json({ error: "Video id required." }, { status: 400 });
  }

  const share = await getPublicShare(videoId);
  if (!share) {
    return NextResponse.json(
      { error: "This video is not publicly shared." },
      { status: 404 }
    );
  }

  return NextResponse.json({ ok: true, share });
}

/** Authenticated publish — sets isPublic on the generation job */
export async function POST(request: Request, context: RouteContext) {
  const auth = await requireApiSession();
  if (!auth.ok) return auth.response;

  const ip = clientIpFromRequest(request) || "unknown";
  const limited = await checkRateLimitAsync(
    `share-publish:${auth.userId}:${ip}`,
    20,
    60_000
  );
  if (!limited.ok) return rateLimitResponse(limited.retryAfterSec);

  const videoId = context.params.videoId?.trim();
  if (!videoId) {
    return NextResponse.json({ error: "Video id required." }, { status: 400 });
  }

  let body: PublishBody;
  try {
    body = (await request.json()) as PublishBody;
  } catch {
    return NextResponse.json({ error: "Invalid request body." }, { status: 400 });
  }

  const videoUrl = body.videoUrl?.trim();
  if (!videoUrl) {
    return NextResponse.json({ error: "Video URL is required to share." }, { status: 400 });
  }

  if (!isAllowedShareVideoUrl(videoUrl)) {
    return NextResponse.json(
      { error: "Video URL must be hosted on RTAS Studio or the configured media host." },
      { status: 400 }
    );
  }

  try {
    const share = await publishPublicShare({
      userId: auth.userId,
      videoId,
      title: body.title?.trim() || "RTAS Studio AI Video",
      prompt: body.prompt ?? null,
      videoUrl,
      durationSeconds: Math.max(0, Number(body.durationSeconds) || 0),
      category: body.category ?? "story",
      visualStyle: body.visualStyle ?? "avatar",
      mode: body.mode ?? "prompt",
    });

    return NextResponse.json({ ok: true, share });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Unable to publish share link.";
    const status = message.includes("only share videos") ? 403 : 500;
    return NextResponse.json({ error: message }, { status });
  }
}
