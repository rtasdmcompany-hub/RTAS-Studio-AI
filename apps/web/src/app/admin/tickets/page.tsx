import type { Metadata } from "next";
import { AdminTicketsClient } from "@/components/admin/AdminTicketsClient";
import { buildPageMetadata } from "@/lib/site-metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Admin · Support tickets",
  description: "Support ticket operations — real tickets only.",
  path: "/admin/tickets",
  noIndex: true,
});

export default function AdminTicketsPage() {
  return <AdminTicketsClient />;
}
