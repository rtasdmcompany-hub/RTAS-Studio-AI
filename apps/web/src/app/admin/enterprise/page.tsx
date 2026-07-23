import type { Metadata } from "next";
import { AdminEnterpriseClient } from "@/components/admin/AdminEnterpriseClient";
import { buildPageMetadata } from "@/lib/site-metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Enterprise CRM",
  description: "RTAS Studio AI enterprise sales pipeline dashboard.",
  path: "/admin/enterprise",
  noIndex: true,
});

export default function AdminEnterprisePage() {
  return <AdminEnterpriseClient />;
}
