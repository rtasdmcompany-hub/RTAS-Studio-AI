"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useId, useMemo, useRef, useState } from "react";
import { useSession } from "next-auth/react";
import { useStudioProfile } from "@/context/StudioProfileContext";
import { TESTER_CREDITS, TESTER_DURATION_DAYS, TESTER_PRICE_USD } from "@rtas/shared";
import type { InAppAnnouncement } from "@/lib/marketing/notifications";

type Notice = {
  id: string;
  tone: "info" | "warn" | "ok";
  text: string;
  href: string;
};

/**
 * Account alerts + system announcements (Notification Center).
 */
export function HeaderNotifications() {
  const { data: session, status } = useSession();
  const { profile } = useStudioProfile();
  const pathname = usePathname() ?? "";
  const menuId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const [announcements, setAnnouncements] = useState<InAppAnnouncement[]>([]);

  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (status !== "authenticated") return;
    let cancelled = false;
    void (async () => {
      try {
        const res = await fetch("/api/user/notifications");
        if (!res.ok) return;
        const json = (await res.json()) as {
          announcements?: InAppAnnouncement[];
        };
        if (!cancelled) setAnnouncements(json.announcements ?? []);
      } catch {
        /* keep account-only notices */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [status]);

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
        text: `No credits — Tester $${TESTER_PRICE_USD} gives ${TESTER_CREDITS}s for ${TESTER_DURATION_DAYS} days.`,
        href: "/pricing",
      });
    } else if (credits <= 0) {
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

    for (const a of announcements.slice(0, 3)) {
      items.push({
        id: `ann-${a.id}`,
        tone: a.kind === "security" || a.kind === "billing" ? "warn" : "info",
        text: a.title,
        href: a.href || "/profile/notifications",
      });
    }

    items.push({
      id: "prefs",
      tone: "info",
      text: "Notification preferences",
      href: "/profile/notifications",
    });
    items.push({
      id: "library",
      tone: "info",
      text: "Open Dashboard for renders, library, and billing.",
      href: "/profile",
    });
    return items.slice(0, 6);
  }, [session?.user, profile, announcements]);

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
        aria-label={warnCount ? `Notifications, ${warnCount} alerts` : "Notifications"}
        onClick={() => setOpen((v) => !v)}
      >
        <span className="studio-notify__bell" aria-hidden>
          ◈
        </span>
        {warnCount > 0 ? (
          <span className="studio-notify__badge">{warnCount > 9 ? "9+" : warnCount}</span>
        ) : null}
      </button>
      {open ? (
        <div className="studio-notify__menu" id={menuId} role="menu">
          <p className="studio-notify__heading">Notifications</p>
          <ul className="studio-notify__list">
            {notices.map((n) => (
              <li key={n.id}>
                <Link
                  href={n.href}
                  className={`studio-notify__item studio-notify__item--${n.tone}`}
                  role="menuitem"
                  onClick={() => setOpen(false)}
                >
                  {n.text}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
