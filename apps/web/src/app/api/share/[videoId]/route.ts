import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth/auth-options";
import { getPublicShare, publishPublicShare } from "@/lib/server/share-store";

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
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json(
      { error: "Sign in to share your studio videos." },
      { status: 401 }
    );
  }

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

  try {
    const share = await publishPublicShare({
      userId: session.user.id,
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
