"use client";

import { usePathname } from "next/navigation";
import { useEffect, useRef, type ReactNode } from "react";
import { AnalyticsEvents, trackClientEvent } from "@/lib/analytics";

/**
 * Route-level page views for primary commercial surfaces.
 * Does not fire fabricated traffic — only records real navigations after mount.
 */
export function AnalyticsProvider({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const lastPath = useRef<string | null>(null);

  useEffect(() => {
    if (!pathname || pathname === lastPath.current) return;
    lastPath.current = pathname;

    if (pathname === "/") {
      trackClientEvent(AnalyticsEvents.HOMEPAGE_VIEWED, { path: pathname });
      return;
    }
    if (pathname === "/pricing" || pathname.startsWith("/pricing/")) {
      trackClientEvent(AnalyticsEvents.PRICING_VIEWED, { path: pathname });
      return;
    }
    if (pathname === "/profile" || pathname.startsWith("/profile/")) {
      trackClientEvent(AnalyticsEvents.DASHBOARD_VIEWED, { path: pathname });
    }
  }, [pathname]);

  return <>{children}</>;
}
