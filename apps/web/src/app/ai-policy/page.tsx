import type { Metadata } from "next";
import { AI_POLICY_INTRO, AI_POLICY_SECTIONS } from "@rtas/shared";
import { LegalLayout } from "@/components/legal/LegalLayout";
import { LegalProse } from "@/components/legal/LegalProse";
import { StructuredData } from "@/components/seo/StructuredData";
import { buildPageMetadata } from "@/lib/site-metadata";
import { breadcrumbSchema } from "@/lib/structured-data";

export const metadata: Metadata = buildPageMetadata({
  title: "AI Usage Policy",
  description:
    "RTAS Studio AI Usage Policy: generate only original, licensed, owned, or authorized content. Identity Preservation for authorized likenesses only.",
  path: "/ai-policy",
  openGraphTitle: "AI Usage Policy · RTAS Studio AI",
  openGraphDescription:
    "Permitted and prohibited AI uses on RTAS Studio AI, including Identity Preservation rules and Merchant of Record compliance.",
});

export default function AiPolicyPage() {
  return (
    <LegalLayout
      title="AI Usage Policy"
      subtitle="Original & authorized content only"
    >
      <StructuredData
        data={breadcrumbSchema([
          { name: "Home", path: "/" },
          { name: "AI Usage Policy", path: "/ai-policy" },
        ])}
      />
      <LegalProse intro={AI_POLICY_INTRO} sections={AI_POLICY_SECTIONS} />
    </LegalLayout>
  );
}
