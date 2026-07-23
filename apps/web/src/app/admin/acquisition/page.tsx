import type { Metadata } from "next";
import { AcquisitionDashboardClient } from "@/components/admin/AcquisitionDashboardClient";
import { buildPageMetadata } from "@/lib/site-metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Customer Acquisition",
  description: "RTAS Studio AI customer acquisition funnel — admin only.",
  path: "/admin/acquisition",
  noIndex: true,
});

export default function AdminAcquisitionPage() {
  return <AcquisitionDashboardClient />;
}
