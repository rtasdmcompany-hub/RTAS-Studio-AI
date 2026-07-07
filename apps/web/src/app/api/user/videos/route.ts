import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { DEFAULT_VIDEO_PAGE_SIZE, MAX_VIDEO_PAGE_SIZE } from "@rtas/shared";
import { authOptions } from "@/lib/auth/auth-options";
import { listUserGenerationJobsPaginated } from "@/lib/server/studio-generation-guard";

export const runtime = "nodejs";

const AUTH_REQUIRED = {
  error: "Authentication required. Please log in to access the studio.",
} as const;

/** Paginated gallery of GenerationJob rows for the authenticated user. */
export async function GET(request: Request) {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json(AUTH_REQUIRED, { status: 401 });
  }

  const { searchParams } = new URL(request.url);
  const cursor = searchParams.get("cursor");
  const limitRaw = Number.parseInt(searchParams.get("limit") ?? "", 10);
  const limit = Number.isFinite(limitRaw)
    ? Math.min(Math.max(limitRaw, 1), MAX_VIDEO_PAGE_SIZE)
    : DEFAULT_VIDEO_PAGE_SIZE;

  const page = await listUserGenerationJobsPaginated(session.user.id, {
    cursor,
    limit,
  });

  return NextResponse.json(page, {
    headers: {
      "Cache-Control": "private, no-store, max-age=0",
    },
  });
}
