import type { Metadata } from "next";
import { COOKIES_INTRO, COOKIE_SECTIONS, PRODUCT_NAME } from "@rtas/shared";
import { LegalLayout } from "@/components/legal/LegalLayout";
import { LegalProse } from "@/components/legal/LegalProse";
import { StructuredData } from "@/components/seo/StructuredData";
import { CookieSettingsButton } from "@/components/marketing/CookieSettingsButton";
import { buildPageMetadata } from "@/lib/site-metadata";
import { breadcrumbSchema } from "@/lib/structured-data";

export const metadata: Metadata = buildPageMetadata({
  title: "Cookie Policy",
  description: `Cookie Policy for ${PRODUCT_NAME} — Necessary, Analytics, and Marketing categories with consent controls.`,
  path: "/cookies",
  openGraphTitle: `Cookie Policy · ${PRODUCT_NAME}`,
  openGraphDescription: `How ${PRODUCT_NAME} uses cookies, local storage, and third-party payment technologies with consent controls.`,
});

export default function CookiesPage() {
  return (
    <LegalLayout
      title="Cookie Policy"
      subtitle="Necessary, Analytics & Marketing categories with consent controls"
    >
      <StructuredData
        data={breadcrumbSchema([
          { name: "Home", path: "/" },
          { name: "Cookie Policy", path: "/cookies" },
        ])}
      />
      <div className="mb-6">
        <CookieSettingsButton label="Manage cookie preferences" />
      </div>
      <LegalProse intro={COOKIES_INTRO} sections={COOKIE_SECTIONS} />
    </LegalLayout>
  );
}
