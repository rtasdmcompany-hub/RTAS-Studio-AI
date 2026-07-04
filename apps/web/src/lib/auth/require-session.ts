import { redirect } from "next/navigation";
import { getServerSession } from "next-auth";
import type { Session } from "next-auth";
import { authOptions } from "@/lib/auth/auth-options";

export function loginRedirectUrl(returnPath = "/studio"): string {
  return `/auth/login?callbackUrl=${encodeURIComponent(returnPath)}`;
}

/** Redirects unauthenticated or unverified users before any page UI renders. */
export async function requireSession(returnPath = "/studio"): Promise<Session> {
  const session = await getServerSession(authOptions);

  if (!session?.user?.id || session.user.emailVerified === false) {
    redirect(loginRedirectUrl(returnPath));
  }

  return session;
}
