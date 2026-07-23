import type { Metadata } from "next";
import { PRODUCT_NAME } from "@rtas/shared";
import { HelpCenterClient } from "./HelpCenterClient";
import { buildPageMetadata } from "@/lib/site-metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Help Center",
  description: `Searchable Help Center for ${PRODUCT_NAME} — Account, Billing, Credits, Video Generation, Templates, AI Models, Enterprise, API, Security, and Technical Issues.`,
  path: "/help",
  openGraphTitle: `Help Center · ${PRODUCT_NAME}`,
});

export default function HelpPage() {
  return <HelpCenterClient />;
}
