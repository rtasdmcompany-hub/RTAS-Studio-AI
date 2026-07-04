import { PRIVACY_INTRO, PRIVACY_SECTIONS } from "@rtas/shared";
import { LegalLayout } from "@/components/legal/LegalLayout";
import { LegalProse } from "@/components/legal/LegalProse";

export default function PrivacyPage() {
  return (
    <LegalLayout
      title="Privacy Policy"
      subtitle="Global data protection, AI processing & cross-border compliance"
    >
      <LegalProse intro={PRIVACY_INTRO} sections={PRIVACY_SECTIONS} />
    </LegalLayout>
  );
}
