import type { Metadata } from "next";
import {
  COMMUNITY_GUIDELINES_INTRO,
  COMMUNITY_GUIDELINES_SECTIONS,
  PRODUCT_NAME,
} from "@rtas/shared";
import { LegalLayout } from "@/components/legal/LegalLayout";
import { LegalProse } from "@/components/legal/LegalProse";
import { StructuredData } from "@/components/seo/StructuredData";
import { buildPageMetadata } from "@/lib/site-metadata";
import { breadcrumbSchema } from "@/lib/structured-data";

export const metadata: Metadata = buildPageMetadata({
  title: "Community Guidelines",
  description: `Community Guidelines for ${PRODUCT_NAME} — respectful use, authorized content, and enforcement.`,
  path: "/community-guidelines",
  openGraphTitle: `Community Guidelines · ${PRODUCT_NAME}`,
  openGraphDescription: `Expectations for respectful, authorized use of ${PRODUCT_NAME}.`,
});

export default function CommunityGuidelinesPage() {
  return (
    <LegalLayout
      title="Community Guidelines"
      subtitle="Respectful, authorized use of Studio, sharing, and support channels"
    >
      <StructuredData
        data={breadcrumbSchema([
          { name: "Home", path: "/" },
          { name: "Community Guidelines", path: "/community-guidelines" },
        ])}
      />
      <LegalProse
        intro={COMMUNITY_GUIDELINES_INTRO}
        sections={COMMUNITY_GUIDELINES_SECTIONS}
      />
    </LegalLayout>
  );
}
