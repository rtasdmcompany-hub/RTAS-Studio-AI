import type { Metadata } from "next";
import { TRUST_SAFETY_INTRO, TRUST_SAFETY_SECTIONS } from "@rtas/shared";
import { LegalLayout } from "@/components/legal/LegalLayout";
import { LegalProse } from "@/components/legal/LegalProse";
import { StructuredData } from "@/components/seo/StructuredData";
import { buildPageMetadata } from "@/lib/site-metadata";
import { breadcrumbSchema } from "@/lib/structured-data";

export const metadata: Metadata = buildPageMetadata({
  title: "Trust & Safety",
  description:
    "RTAS Studio AI Trust & Safety: prohibited uses including face swapping, celebrity impersonation, deepfake abuse, and identity fraud.",
  path: "/trust-safety",
});

export default function TrustSafetyPage() {
  return (
    <LegalLayout
      title="Trust & Safety"
      subtitle="Authorized creativity only — no face swapping, celebrity cloning, or deepfake abuse"
    >
      <StructuredData
        data={breadcrumbSchema([
          { name: "Home", path: "/" },
          { name: "Trust & Safety", path: "/trust-safety" },
        ])}
      />
      <LegalProse intro={TRUST_SAFETY_INTRO} sections={TRUST_SAFETY_SECTIONS} />
    </LegalLayout>
  );
}
