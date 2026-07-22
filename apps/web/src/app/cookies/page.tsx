import type { Metadata } from "next";
import { COOKIES_INTRO, COOKIE_SECTIONS, PRODUCT_NAME } from "@rtas/shared";
import { LegalLayout } from "@/components/legal/LegalLayout";
import { LegalProse } from "@/components/legal/LegalProse";
import { StructuredData } from "@/components/seo/StructuredData";
import { buildPageMetadata } from "@/lib/site-metadata";
import { breadcrumbSchema } from "@/lib/structured-data";

export const metadata: Metadata = buildPageMetadata({
  title: "Cookie Policy",
  description: `Cookie Policy for ${PRODUCT_NAME} — consent, essential cookies, and third-party payment technologies.`,
  path: "/cookies",
  openGraphTitle: `Cookie Policy · ${PRODUCT_NAME}`,
  openGraphDescription: `How ${PRODUCT_NAME} uses cookies, local storage, and third-party payment technologies with consent controls.`,
});

export default function CookiesPage() {
  return (
    <LegalLayout
      title="Cookie Policy"
      subtitle="Consent, essential cookies & third-party payment technologies"
    >
      <StructuredData
        data={breadcrumbSchema([
          { name: "Home", path: "/" },
          { name: "Cookie Policy", path: "/cookies" },
        ])}
      />
      <LegalProse intro={COOKIES_INTRO} sections={COOKIE_SECTIONS} />
    </LegalLayout>
  );
}
