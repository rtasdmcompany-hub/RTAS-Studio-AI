import type { Metadata } from "next";
import { PromotionsAdminClient } from "@/components/admin/PromotionsAdminClient";
import { buildPageMetadata } from "@/lib/site-metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Promotions admin",
  description: "Revenue Promotion Engine control center for RTAS Studio AI.",
  path: "/admin/promotions",
  noIndex: true,
});

export default function AdminPromotionsPage() {
  return <PromotionsAdminClient />;
}
