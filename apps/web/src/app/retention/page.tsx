import type { Metadata } from "next";
import { PRODUCT_NAME } from "@rtas/shared";
import { RetentionClient } from "./RetentionClient";
import { buildPageMetadata } from "@/lib/site-metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Retention Center",
  description: `Usage insights, upgrades, feature discovery, tips, learning, referral, and milestones for ${PRODUCT_NAME}. Sign-in required. Real account data only.`,
  path: "/retention",
  noIndex: true,
});

export default function RetentionPage() {
  return <RetentionClient />;
}
