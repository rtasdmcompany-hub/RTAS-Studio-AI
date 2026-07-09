import { CampaignStatus } from "@/generated/prisma";
import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth/auth-options";
import { prisma, isPrismaConfigured } from "@/lib/prisma";
import {
  assertTesterGenerationAllowed,
  TESTER_LIMIT_REACHED_MESSAGE,
} from "@/lib/server/tester-subscription";
import { getServerProfile } from "@/lib/server/profile-store";

export const runtime = "nodejs";

export async function POST(request: Request) {
  const session = await getServerSession(authOptions);
  const userId = session?.user?.id;

  if (!userId) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const body = (await request.json()) as {
      title?: string;
      description?: string | null;
      keywords?: string | null;
      videoFileName?: string;
      thumbnailFileName?: string | null;
      videoDurationSeconds?: number;
      mode?: "publish" | "schedule";
      scheduledAt?: string | null;
    };

    if (!body.title?.trim()) {
      return NextResponse.json({ error: "Title is required." }, { status: 400 });
    }
    if (!body.videoFileName?.trim()) {
      return NextResponse.json({ error: "Video file is required." }, { status: 400 });
    }

    const duration = Math.max(1, body.videoDurationSeconds ?? 30);
    const profile = await getServerProfile(userId);

    if (body.mode === "publish" && profile.tier === "tester") {
      try {
        await assertTesterGenerationAllowed(userId, duration);
      } catch {
        return NextResponse.json({ error: TESTER_LIMIT_REACHED_MESSAGE }, { status: 403 });
      }
    }

    const payload = {
      title: body.title.trim(),
      description: [body.description, body.keywords ? `Tags: ${body.keywords}` : null]
        .filter(Boolean)
        .join("\n\n") || null,
      rawVideoUrl: `pending://${encodeURIComponent(body.videoFileName.trim())}`,
      videoDuration: duration,
      status:
        body.mode === "schedule" ? CampaignStatus.PENDING : CampaignStatus.PROCESSING,
    };

    if (isPrismaConfigured()) {
      await prisma.campaign.create({
        data: {
          userId,
          ...payload,
        },
      });
    }

    const scheduleNote =
      body.mode === "schedule" && body.scheduledAt
        ? ` Scheduled for ${new Date(body.scheduledAt).toLocaleString()}.`
        : "";

    return NextResponse.json({
      ok: true,
      message:
        body.mode === "schedule"
          ? `Campaign queued for scheduled publishing.${scheduleNote}`
          : "Campaign queued for publishing to connected platforms.",
      campaign: payload,
      thumbnailFileName: body.thumbnailFileName ?? null,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Could not create campaign.";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
