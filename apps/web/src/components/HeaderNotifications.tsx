"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useId, useMemo, useRef, useState } from "react";
import { useSession } from "next-auth/react";
import { useStudioProfile } from "@/context/StudioProfileContext";
import { FREE_TRIAL_DURATION_SECONDS } from "@rtas/shared";

type Notice = { id: string; tone: "info" | "warn" | "ok"; text: string; href: string };

/**
 * Lightweight account alerts — mirrors dashboard signals without a separate inbox API.
 */
export function HeaderNotifications() {
  const { data: session, status } = useSession();
  const { profile } = useStudioProfile();
  const pathname = usePathname() ?? "";
  const menuId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);

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

  const notices = useMemo((): Notice[] => {
    if (!session?.user || !profile) return [];
    const items: Notice[] = [];
    const credits = profile.credits ?? 0;
    if (credits <= 0 && !profile.subscriptionActive) {
      items.push({
        id: "credits",
        tone: "warn",
        text: "Credits depleted — upgrade to keep rendering.",
        href: "/pricing",
      });
    } else if (
      profile.creditsExpireAt &&
      new Date(profile.creditsExpireAt).getTime() - Date.now() < 7 * 24 * 60 * 60 * 1000
    ) {
      items.push({
        id: "expiry",
        tone: "warn",
        text: `Credits expire ${new Date(profile.creditsExpireAt).toLocaleDateString()}`,
        href: "/pricing",
      });
    }
    if (!profile.freeTrialUsed && !profile.hasUsedFreeTrial) {
      items.push({
        id: "trial",
        tone: "ok",
        text: `${FREE_TRIAL_DURATION_SECONDS}s evaluation preview still available`,
        href: "/studio",
      });
    }
    items.push({
      id: "library",
      tone: "info",
      text: "Open Dashboard for renders, library, and billing.",
      href: "/profile",
    });
    return items.slice(0, 4);
  }, [session?.user, profile]);

  if (status === "loading") {
    return <span className="studio-notify-skeleton" aria-hidden />;
  }

  if (!session?.user) {
    return null;
  }

  const warnCount = notices.filter((n) => n.tone === "warn").length;

  return (
    <div className="studio-notify" ref={rootRef}>
      <button
        type="button"
        className="studio-notify__trigger"
        aria-expanded={open}
        aria-controls={menuId}
        aria-haspopup="menu"
        aria-label={warnCount ? `Notifications, ${warnCount} alerts` : "Notifications"}
        onClick={() => setOpen((v) => !v)}
      >
        <span aria-hidden>🔔</span>
        {warnCount > 0 ? <span className="studio-notify__dot" aria-hidden /> : null}
      </button>
      {open ? (
        <div id={menuId} className="studio-notify__menu" role="menu">
          <p className="studio-notify__title">Notifications</p>
          {notices.length === 0 ? (
            <p className="studio-notify__empty">You are all caught up.</p>
          ) : (
            notices.map((n) => (
              <Link
                key={n.id}
                href={n.href}
                className={`studio-notify__item studio-notify__item--${n.tone}`}
                role="menuitem"
                onClick={() => setOpen(false)}
              >
                {n.text}
              </Link>
            ))
          )}
          <Link
            href="/profile"
            className="studio-notify__footer"
            role="menuitem"
            onClick={() => setOpen(false)}
          >
            Open Dashboard →
          </Link>
        </div>
      ) : null}
    </div>
  );
}
