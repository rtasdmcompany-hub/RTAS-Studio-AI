import { TERMS_SECTIONS } from "@rtas/shared";
import { LegalLayout } from "@/components/legal/LegalLayout";

export default function TermsPage() {
  return (
    <LegalLayout
      title="Terms of Service"
      subtitle="International use, subscriptions, commercial rights & preview restrictions"
    >
      <div className="legal-prose">
        <p className="legal-lead">
          Please read these Terms carefully. They govern your access to RTAS Studio AI
          and define when commercial rights transfer to you.
        </p>
        {TERMS_SECTIONS.map((s) => (
          <section key={s.title} id={s.title.replace(/\s+/g, "-").toLowerCase()}>
            <h2>{s.title}</h2>
            <p>{s.body}</p>
          </section>
        ))}
      </div>
    </LegalLayout>
  );
}
