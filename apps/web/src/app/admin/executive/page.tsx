import type { Metadata } from "next";
import { ExecutiveDashboardClient } from "@/components/admin/ExecutiveDashboardClient";
import { buildPageMetadata } from "@/lib/site-metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Executive BI",
  description: "RTAS Studio AI executive business intelligence — admin only.",
  path: "/admin/executive",
  noIndex: true,
});

export default function AdminExecutivePage() {
  return <ExecutiveDashboardClient />;
}
