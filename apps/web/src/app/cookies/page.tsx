import { COOKIES_INTRO, COOKIE_SECTIONS } from "@rtas/shared";
import { LegalLayout } from "@/components/legal/LegalLayout";
import { LegalProse } from "@/components/legal/LegalProse";

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
