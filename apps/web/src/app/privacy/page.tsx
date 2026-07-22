import type { Metadata } from "next";
import { PRIVACY_INTRO, PRIVACY_SECTIONS, PRODUCT_NAME } from "@rtas/shared";
import { LegalLayout } from "@/components/legal/LegalLayout";
import { LegalProse } from "@/components/legal/LegalProse";
import { StructuredData } from "@/components/seo/StructuredData";
import { buildPageMetadata } from "@/lib/site-metadata";
import { breadcrumbSchema } from "@/lib/structured-data";

export const metadata: Metadata = buildPageMetadata({
  title: "Privacy Policy",
  description: `Privacy Policy for ${PRODUCT_NAME} — how we collect, use, and protect your data, including Paddle payment processing.`,
  path: "/privacy",
  openGraphTitle: `Privacy Policy · ${PRODUCT_NAME}`,
  openGraphDescription: `How ${PRODUCT_NAME} collects, uses, and protects personal data under GDPR, UK GDPR, and CCPA frameworks.`,
});

export default function PrivacyPage() {
  return (
    <LegalLayout
      title="Privacy Policy"
      subtitle="Global data protection, AI processing & cross-border compliance"
    >
      <StructuredData
        data={breadcrumbSchema([
          { name: "Home", path: "/" },
          { name: "Privacy Policy", path: "/privacy" },
        ])}
      />
      <LegalProse intro={PRIVACY_INTRO} sections={PRIVACY_SECTIONS} />
    </LegalLayout>
  );
}
