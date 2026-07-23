import type { Metadata } from "next";
import { PRODUCT_NAME } from "@rtas/shared";
import { HealthClient } from "./HealthClient";
import { buildPageMetadata } from "@/lib/site-metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Customer Health",
  description: `Your ${PRODUCT_NAME} account health — age, verification, subscription, credits, projects, videos, login, usage, tickets, and rule-based risk. Real data only.`,
  path: "/profile/health",
  noIndex: true,
});

export default function ProfileHealthPage() {
  return <HealthClient />;
}
