"use client";

import { usePathname } from "next/navigation";
import { SiteHeader } from "@/components/SiteHeader";
import { CreditsPill } from "@/components/CreditsPill";

const HIDE_HEADER_PREFIXES = ["/share/"] as const;

/** Single global navbar — mounted from root layout on every route. */
export function GlobalSiteHeader() {
  const pathname = usePathname() ?? "";

  if (HIDE_HEADER_PREFIXES.some((prefix) => pathname.startsWith(prefix))) {
    return null;
  }

  const isStudio = pathname.startsWith("/studio");

  return (
    <SiteHeader
      className={isStudio ? "rtas-header--studio" : undefined}
      actionsSlot={isStudio ? <CreditsPill /> : undefined}
      authVariant={isStudio ? "studio" : "landing"}
    />
  );
}
