"use client";

import { usePathname } from "next/navigation";
import { getPageBackgroundVideo } from "@/lib/preview-showcase";
import { PageVideoBackground } from "./PageVideoBackground";

/** Route-specific full-page video behind marketing/auth shells. */
export function MarketingPageVideoBackground() {
  const pathname = usePathname() ?? "";
  const src = getPageBackgroundVideo(pathname);
  if (!src) return null;
  return <PageVideoBackground src={src} className="rtas-marketing-page-video" />;
}
