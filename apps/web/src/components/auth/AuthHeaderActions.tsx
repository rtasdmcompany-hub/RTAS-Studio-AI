"use client";

import { usePathname } from "next/navigation";
import { signOut, useSession } from "next-auth/react";
import { Button, ButtonLink } from "@rtas/ui";
import { headerUserLabel, profileDisplayName } from "@/lib/user-display-name";

type Variant = "studio" | "landing";

const AUTH_GUEST_ONLY_PATHS = ["/auth/signup", "/auth/check-email"];

export function AuthHeaderActions({ variant = "studio" }: { variant?: Variant }) {
  const { data: session, status } = useSession();
  const pathname = usePathname();
  const forceGuest =
    AUTH_GUEST_ONLY_PATHS.some((path) => pathname?.startsWith(path)) ||
    session?.user?.emailVerified === false;

  if (status === "loading" && pathname && AUTH_GUEST_ONLY_PATHS.some((p) => pathname.startsWith(p))) {
    return (
      <span
        className="inline-block h-8 w-20 animate-pulse rounded-lg bg-white/10"
        aria-busy="true"
        aria-label="Loading account actions"
        role="status"
      />
    );
  }

  if (session?.user && !forceGuest) {
    const label = headerUserLabel(session.user);
    const fullName = profileDisplayName(session.user);
    return (
      <>
        <span className="auth-user-pill" title={fullName}>
          {label}
        </span>
        <ButtonLink href="/profile" variant="ghost" className="rtas-header__profile-link">
          Dashboard
        </ButtonLink>
        <Button variant="ghost" onClick={() => signOut({ callbackUrl: "/" })}>
          Sign out
        </Button>
      </>
    );
  }

  const loginHref =
    variant === "studio"
      ? "/auth/login?callbackUrl=%2Fstudio"
      : "/auth/login";

  return (
    <>
      <ButtonLink href={loginHref} variant="ghost">
        Sign in
      </ButtonLink>
      <ButtonLink
        href={
          variant === "studio"
            ? "/auth/signup?callbackUrl=%2Fstudio"
            : "/auth/signup"
        }
        variant="primary"
        className="auth-signup-btn"
      >
        Sign up
      </ButtonLink>
    </>
  );
}
