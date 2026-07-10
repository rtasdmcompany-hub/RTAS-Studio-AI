"use client";

import { useEffect, type ReactNode } from "react";
import { useSearchParams } from "next/navigation";
import { signOut, useSession } from "next-auth/react";
import { AuthSkeleton, StudioSkeleton } from "@/components/ui/skeletons";

type Mode = "signup" | "login" | "check-email";

function resolveCallbackPath(raw: string | null): string {
  if (raw && raw.startsWith("/") && !raw.startsWith("//")) return raw;
  // Default post-auth landing: dashboard with welcome guidance (60-second clarity).
  return "/profile?welcome=1";
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
    return <AuthSkeleton />;
  }

  if (shouldLeaveLogin) {
    return <StudioSkeleton />;
  }

  return <>{children}</>;
}

export function resolveAuthCallbackUrl(
  raw: string | null,
  fallback = "/profile?welcome=1"
): string {
  return resolveCallbackPath(raw) || fallback;
}
