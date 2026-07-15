"use client";

import Link from "next/link";
import { useEffect, useId, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import { signOut, useSession } from "next-auth/react";
import { ButtonLink } from "@rtas/ui";
import { headerUserLabel, profileDisplayName } from "@/lib/user-display-name";

type Variant = "studio" | "landing";

const AUTH_GUEST_ONLY_PATHS = ["/auth/signup", "/auth/check-email"];

function initialsFromLabel(label: string): string {
  const parts = label.trim().split(/\s+/).filter(Boolean);
  if (parts.length >= 2) {
    return `${parts[0][0] ?? ""}${parts[1][0] ?? ""}`.toUpperCase();
  }
  return (label.slice(0, 2) || "RT").toUpperCase();
}

export function AuthHeaderActions({ variant = "studio" }: { variant?: Variant }) {
  const { data: session, status } = useSession();
  const pathname = usePathname() ?? "";
  const menuId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);

  const forceGuest =
    AUTH_GUEST_ONLY_PATHS.some((path) => pathname.startsWith(path)) ||
    session?.user?.emailVerified === false;

  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    const onPointer = (e: MouseEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    window.addEventListener("mousedown", onPointer);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("mousedown", onPointer);
    };
  }, [open]);

  // Always skeleton while session resolves — avoids guest/signed-in hydration mismatch
  if (status === "loading") {
    return (
      <span
        className="studio-profile-skeleton"
        aria-busy="true"
        aria-label="Loading account actions"
        role="status"
      />
    );
  }

  if (session?.user && !forceGuest) {
    const label = headerUserLabel(session.user);
    const fullName = profileDisplayName(session.user);
    const email = session.user.email ?? "";
    const initials = initialsFromLabel(fullName || label);

    return (
      <div className="studio-profile" ref={rootRef}>
        <button
          type="button"
          className="studio-profile__trigger"
          aria-expanded={open}
          aria-controls={menuId}
          aria-haspopup="menu"
          onClick={() => setOpen((v) => !v)}
        >
          <span className="studio-profile__avatar" aria-hidden>
            {initials}
          </span>
          <span className="studio-profile__meta">
            <span className="studio-profile__name">{fullName || label}</span>
            {email ? <span className="studio-profile__email">{email}</span> : null}
          </span>
          <span className="studio-profile__caret" aria-hidden>
            ▾
          </span>
        </button>
        {open ? (
          <div id={menuId} className="studio-profile__menu" role="menu">
            <div className="studio-profile__menu-head">
              <p className="studio-profile__menu-name">{fullName || label}</p>
              {email ? <p className="studio-profile__menu-email">{email}</p> : null}
            </div>
            <Link
              href="/profile"
              className="studio-profile__item"
              role="menuitem"
              onClick={() => setOpen(false)}
            >
              Dashboard
            </Link>
            <Link
              href="/pricing"
              className="studio-profile__item"
              role="menuitem"
              onClick={() => setOpen(false)}
            >
              Plans & billing
            </Link>
            <Link
              href="/help"
              className="studio-profile__item"
              role="menuitem"
              onClick={() => setOpen(false)}
            >
              Help Center
            </Link>
            <button
              type="button"
              className="studio-profile__item studio-profile__item--danger"
              role="menuitem"
              onClick={() => void signOut({ callbackUrl: "/" })}
            >
              Sign out
            </button>
          </div>
        ) : null}
      </div>
    );
  }

  const welcomeCallback = encodeURIComponent("/profile?welcome=1");

  return (
    <div className="studio-auth-guest">
      <ButtonLink href={`/auth/login?callbackUrl=${welcomeCallback}`} variant="ghost">
        Sign in
      </ButtonLink>
      <ButtonLink
        href={`/auth/signup?callbackUrl=${welcomeCallback}`}
        variant={variant === "studio" ? "lavender" : "primary"}
        className="auth-signup-btn"
      >
        Sign up
      </ButtonLink>
    </div>
  );
}
