import type { Metadata } from "next";
import { PRODUCT_NAME } from "@rtas/shared";
import { TicketsClient } from "./TicketsClient";
import { buildPageMetadata } from "@/lib/site-metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Support Tickets",
  description: `Create and track support tickets for ${PRODUCT_NAME}. Sign-in required. No fabricated tickets.`,
  path: "/tickets",
  noIndex: true,
});

export default function TicketsPage() {
  return <TicketsClient />;
}
