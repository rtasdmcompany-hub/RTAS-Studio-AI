import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth/auth-options";
import {
  bindSocialToken,
  disconnectSocialToken,
  DuplicatePlatformBindingError,
  getConnectedSocialChannels,
  SocialRegistryNotConfiguredError,
} from "@/lib/server/social-registry";

export const runtime = "nodejs";

export async function GET() {
  const session = await getServerSession(authOptions);
  const userId = session?.user?.id;

  if (!userId) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const channels = await getConnectedSocialChannels(userId);
    return NextResponse.json({ channels });
  } catch (error) {
    if (error instanceof SocialRegistryNotConfiguredError) {
      return NextResponse.json({ error: error.message }, { status: 503 });
    }
    const message =
      error instanceof Error ? error.message : "Could not load social channels.";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

export async function POST(request: Request) {
  const session = await getServerSession(authOptions);
  const userId = session?.user?.id;

  if (!userId) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const body = (await request.json()) as {
      platform?: string;
      accessToken?: string;
      refreshToken?: string | null;
      expiresAt?: string | null;
      allowReplace?: boolean;
    };

    if (!body.platform || !body.accessToken) {
      return NextResponse.json(
        { error: "platform and accessToken are required." },
        { status: 400 }
      );
    }

    const token = await bindSocialToken({
      userId,
      platform: body.platform,
      accessToken: body.accessToken,
      refreshToken: body.refreshToken ?? null,
      expiresAt: body.expiresAt ?? null,
      allowReplace: body.allowReplace === true,
    });

    const channels = await getConnectedSocialChannels(userId);
    return NextResponse.json({
      ok: true,
      token: {
        id: token.id,
        platform: token.platform,
        expiresAt: token.expiresAt?.toISOString() ?? null,
      },
      channels,
    });
  } catch (error) {
    if (error instanceof DuplicatePlatformBindingError) {
      return NextResponse.json({ error: error.message }, { status: 409 });
    }
    if (error instanceof SocialRegistryNotConfiguredError) {
      return NextResponse.json({ error: error.message }, { status: 503 });
    }
    const message =
      error instanceof Error ? error.message : "Could not bind social token.";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

export async function DELETE(request: Request) {
  const session = await getServerSession(authOptions);
  const userId = session?.user?.id;

  if (!userId) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const { searchParams } = new URL(request.url);
    const platform = searchParams.get("platform");

    if (!platform) {
      return NextResponse.json({ error: "platform is required." }, { status: 400 });
    }

    await disconnectSocialToken({ userId, platform });
    const channels = await getConnectedSocialChannels(userId);
    return NextResponse.json({ ok: true, channels });
  } catch (error) {
    if (error instanceof SocialRegistryNotConfiguredError) {
      return NextResponse.json({ error: error.message }, { status: 503 });
    }
    const message =
      error instanceof Error ? error.message : "Could not disconnect social token.";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
