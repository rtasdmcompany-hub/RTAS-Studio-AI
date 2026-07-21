import type { Metadata } from "next";
import { AdminDashboardClient } from "@/components/admin/AdminDashboardClient";
import { buildPageMetadata } from "@/lib/site-metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Admin",
  description: "RTAS Studio AI operations dashboard.",
  path: "/admin",
  noIndex: true,
});

export default function AdminPage() {
  return <AdminDashboardClient />;
}
