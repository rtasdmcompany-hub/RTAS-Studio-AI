import type { Metadata } from "next";
import { RevenueOpsDashboardClient } from "@/components/admin/RevenueOpsDashboardClient";
import { buildPageMetadata } from "@/lib/site-metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Revenue operations",
  description: "RTAS Studio AI RevOps dashboard — live MRR, signups, credits, and transactions.",
  path: "/admin/revenue",
  noIndex: true,
});

export default function AdminRevenuePage() {
  return <RevenueOpsDashboardClient />;
}
