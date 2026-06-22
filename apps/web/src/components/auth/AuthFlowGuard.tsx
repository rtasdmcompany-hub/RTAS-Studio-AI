"use client";

import { useEffect, type ReactNode } from "react";
import { useSearchParams } from "next/navigation";
import { signOut, useSession } from "next-auth/react";

type Mode = "signup" | "login" | "check-email";

function resolveCallbackPath(raw: string | null): string {
  if (raw && raw.startsWith("/") && !raw.startsWith("//")) return raw;
  return "/studio";
}

export function AuthFlowGuard({
  mode,
  children,
}: {
  mode: Mode;
  children?: ReactNode;
}) {
  const { data: session, status } = useSession();
  const searchParams = useSearchParams();
  const callbackPath = resolveCallbackPath(searchParams.get("callbackUrl"));

  const shouldLeaveLogin =
    mode === "login" &&
    status === "authenticated" &&
    session?.user?.emailVerified !== false;

  useEffect(() => {
    if (status === "loading") return;

    if (status === "authenticated") {
      if (mode === "signup" || mode === "check-email") {
        void signOut({ redirect: false });
        return;
      }

      if (shouldLeaveLogin) {
        window.location.replace(callbackPath);
      }
    }
  }, [callbackPath, mode, shouldLeaveLogin, status]);

  if (mode === "login" && status === "loading") {
    return <p className="auth-loading">Loading…</p>;
  }

  if (shouldLeaveLogin) {
    return <p className="auth-loading">Opening your workspace…</p>;
  }

  return <>{children}</>;
}

export function resolveAuthCallbackUrl(raw: string | null, fallback = "/studio"): string {
  return resolveCallbackPath(raw) || fallback;
}
