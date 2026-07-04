"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { signOut, useSession } from "next-auth/react";

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
    const label = session.user.name?.split(" ")[0] ?? "Account";
    return (
      <>
        <span className="auth-user-pill" title={session.user.email ?? undefined}>
          {label}
        </span>
        <Link href="/profile" className="btn-ghost rtas-header__profile-link">
          Profile
        </Link>
        <button
          type="button"
          className="btn-ghost"
          onClick={() => signOut({ callbackUrl: "/" })}
        >
          Sign out
        </button>
      </>
    );
  }

  const loginHref =
    variant === "studio"
      ? "/auth/login?callbackUrl=%2Fstudio"
      : "/auth/login";

  return (
    <>
      <Link href={loginHref} className="btn-ghost">
        Sign in
      </Link>
      <Link
        href={
          variant === "studio"
            ? "/auth/signup?callbackUrl=%2Fstudio"
            : "/auth/signup"
        }
        className="btn-primary auth-signup-btn"
      >
        Sign up
      </Link>
    </>
  );
}
