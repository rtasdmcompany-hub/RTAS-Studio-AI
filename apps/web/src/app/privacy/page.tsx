import { PRIVACY_SECTIONS } from "@rtas/shared";
import { LegalLayout } from "@/components/legal/LegalLayout";

export default function PrivacyPage() {
  return (
    <LegalLayout
      title="Privacy Policy"
      subtitle="How RTAS Studio AI collects, uses, and protects your data"
    >
      <div className="legal-prose">
        {PRIVACY_SECTIONS.map((s) => (
          <section key={s.title}>
            <h2>{s.title}</h2>
            <p>{s.body}</p>
          </section>
        ))}
      </div>
    </LegalLayout>
  );
}
