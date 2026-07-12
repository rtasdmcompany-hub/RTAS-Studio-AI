"use client";

import { usePathname } from "next/navigation";
import { SiteHeader } from "@/components/SiteHeader";
import { CreditsPill } from "@/components/CreditsPill";

const HIDE_HEADER_PREFIXES = ["/share/"] as const;

/** Single global navbar — premium chrome on every route. */
export function GlobalSiteHeader() {
  const pathname = usePathname() ?? "";

  if (HIDE_HEADER_PREFIXES.some((prefix) => pathname.startsWith(prefix))) {
    return null;
  }

  const isStudio = pathname.startsWith("/studio");
  const showCredits = isStudio || pathname.startsWith("/profile");

  return (
    <SiteHeader
      actionsSlot={showCredits ? <CreditsPill /> : undefined}
      authVariant={isStudio || pathname.startsWith("/profile") ? "studio" : "landing"}
    />
  );
}
