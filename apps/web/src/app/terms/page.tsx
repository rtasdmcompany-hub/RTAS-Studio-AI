import { TERMS_INTRO, TERMS_SECTIONS } from "@rtas/shared";
import { LegalLayout } from "@/components/legal/LegalLayout";
import { LegalProse } from "@/components/legal/LegalProse";

export default function TermsPage() {
  return (
    <LegalLayout
      title="Terms of Service"
      subtitle="Global subscription terms, commercial licensing & international payment compliance"
    >
      <LegalProse intro={TERMS_INTRO} sections={TERMS_SECTIONS} />
    </LegalLayout>
  );
}
