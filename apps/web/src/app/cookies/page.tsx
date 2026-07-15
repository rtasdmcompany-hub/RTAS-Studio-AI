import type { Metadata } from "next";
import { COOKIES_INTRO, COOKIE_SECTIONS, PRODUCT_NAME } from "@rtas/shared";
import { LegalLayout } from "@/components/legal/LegalLayout";
import { LegalProse } from "@/components/legal/LegalProse";

export const metadata: Metadata = {
  title: "Cookie Policy",
  description: `Cookie Policy for ${PRODUCT_NAME} — consent, essential cookies, and third-party payment technologies.`,
};

export default function CookiesPage() {
  return (
    <LegalLayout
      title="Cookie Policy"
      subtitle="Consent, essential cookies & third-party payment technologies"
    >
      <LegalProse intro={COOKIES_INTRO} sections={COOKIE_SECTIONS} />
    </LegalLayout>
  );
}
