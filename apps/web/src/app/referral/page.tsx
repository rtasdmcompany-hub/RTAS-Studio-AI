import type { Metadata } from "next";
import { PRODUCT_NAME } from "@rtas/shared";
import { ReferralClient } from "@/components/marketing/ReferralClient";
import { buildPageMetadata } from "@/lib/site-metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Referral program",
  description: `Invite creators to ${PRODUCT_NAME}. Proposed rewards — tracking UI live.`,
  path: "/referral",
});

export default function ReferralPage() {
  return <ReferralClient />;
}
