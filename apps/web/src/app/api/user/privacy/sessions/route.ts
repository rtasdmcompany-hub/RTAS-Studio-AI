import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth/auth-options";
import { requireApiSession } from "@/lib/server/api-auth";
import { isPrismaConfigured, prisma } from "@/lib/prisma";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/**
 * Session / auth posture for Privacy & Security settings.
 * JWT strategy — no server-side session table; reports current session + account auth facts.
 * GET /api/user/privacy/sessions
 */
export async function GET() {
  const auth = await requireApiSession({ requireEmailVerified: false });
  if (!auth.ok) return auth.response;

  const session = await getServerSession(authOptions);
  let hasPassword = false;
  let provider = "credentials";
  let lastLoginAt: string | null = null;
  let emailVerified = session?.user?.emailVerified !== false;

  if (isPrismaConfigured()) {
    const user = await prisma.user.findUnique({
      where: { id: auth.userId },
      select: {
        passwordHash: true,
        provider: true,
        lastLoginAt: true,
        emailVerified: true,
      },
    });
    if (user) {
      hasPassword = Boolean(user.passwordHash);
      provider = user.provider;
      lastLoginAt = user.lastLoginAt?.toISOString() ?? null;
      emailVerified = user.emailVerified;
    }
  }

  return NextResponse.json({
    ok: true,
    strategy: "jwt",
    note: "Sessions are JWT-based (up to 30 days). There is no multi-device session list yet — sign out clears this browser; change password invalidates credentials for new logins. Multi-device revocation is Roadmap.",
    current: {
      userId: auth.userId,
      email: session?.user?.email ?? null,
      name: session?.user?.name ?? null,
      emailVerified,
      provider,
      hasPassword,
      lastLoginAt,
      twoFactorEnabled: false,
      twoFactorStatus: "roadmap" as const,
    },
  });
}
