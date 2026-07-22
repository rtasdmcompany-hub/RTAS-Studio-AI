import type { Metadata } from "next";
import { TERMS_INTRO, TERMS_SECTIONS } from "@rtas/shared";
import { LegalLayout } from "@/components/legal/LegalLayout";
import { LegalProse } from "@/components/legal/LegalProse";
import { StructuredData } from "@/components/seo/StructuredData";
import { buildPageMetadata } from "@/lib/site-metadata";
import { breadcrumbSchema } from "@/lib/structured-data";

export const metadata: Metadata = buildPageMetadata({
  title: "Terms of Service",
  description:
    "Terms of Service for RTAS Studio AI — plans, credits, Merchant of Record (Paddle) billing, Acceptable Use, and commercial licensing.",
  path: "/terms",
  openGraphTitle: "Terms of Service · RTAS Studio AI",
  openGraphDescription:
    "Subscription terms, Acceptable Use, Paddle Merchant of Record billing, and commercial licensing for RTAS Studio AI.",
});

export default function TermsPage() {
  return (
    <LegalLayout
      title="Terms of Service"
      subtitle="Global subscription terms, commercial licensing & international payment compliance"
    >
      <StructuredData
        data={breadcrumbSchema([
          { name: "Home", path: "/" },
          { name: "Terms of Service", path: "/terms" },
        ])}
      />
      <LegalProse intro={TERMS_INTRO} sections={TERMS_SECTIONS} />
    </LegalLayout>
  );
}
