import type { Metadata } from "next";
import { MarketingAdminClient } from "@/components/admin/MarketingAdminClient";
import { buildPageMetadata } from "@/lib/site-metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Marketing Admin",
  description: "RTAS Studio AI email marketing and campaign operations.",
  path: "/admin/marketing",
  noIndex: true,
});

export default function AdminMarketingPage() {
  return <MarketingAdminClient />;
}
