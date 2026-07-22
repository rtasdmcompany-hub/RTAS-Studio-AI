import type { Metadata } from "next";
import { REFUND_INTRO, REFUND_SECTIONS } from "@rtas/shared";
import { LegalLayout } from "@/components/legal/LegalLayout";
import { LegalProse } from "@/components/legal/LegalProse";
import { StructuredData } from "@/components/seo/StructuredData";
import { buildPageMetadata } from "@/lib/site-metadata";
import { breadcrumbSchema } from "@/lib/structured-data";

export const metadata: Metadata = buildPageMetadata({
  title: "Refund Policy",
  description:
    "RTAS Studio AI refund policy for digital credits, subscriptions, and Merchant of Record (Paddle) billing.",
  path: "/refund",
  openGraphTitle: "Refund Policy · RTAS Studio AI",
  openGraphDescription:
    "How refunds, cancellations, and chargebacks work for RTAS Studio AI purchases sold by Paddle as Merchant of Record.",
});

export default function RefundPage() {
  return (
    <LegalLayout
      title="Refund Policy"
      subtitle="Billing, digital credits & Merchant-of-Record refunds"
    >
      <StructuredData
        data={breadcrumbSchema([
          { name: "Home", path: "/" },
          { name: "Refund Policy", path: "/refund" },
        ])}
      />
      <LegalProse intro={REFUND_INTRO} sections={REFUND_SECTIONS} />
    </LegalLayout>
  );
}
