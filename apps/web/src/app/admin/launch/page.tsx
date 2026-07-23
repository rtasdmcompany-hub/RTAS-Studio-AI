import type { Metadata } from "next";
import { ExecutiveLaunchDashboardClient } from "@/components/admin/ExecutiveLaunchDashboardClient";
import { buildPageMetadata } from "@/lib/site-metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Executive Launch",
  description: "RTAS Studio AI executive launch readiness — admin only.",
  path: "/admin/launch",
  noIndex: true,
});

export default function AdminLaunchPage() {
  return <ExecutiveLaunchDashboardClient />;
}
