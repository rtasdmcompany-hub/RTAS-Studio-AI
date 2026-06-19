import { COOKIE_SECTIONS } from "@rtas/shared";
import { LegalLayout } from "@/components/legal/LegalLayout";

export default function CookiesPage() {
  return (
    <LegalLayout
      title="Cookie Policy"
      subtitle="How we use cookies and similar technologies"
    >
      <div className="legal-prose">
        <p className="legal-lead">
          This policy explains how RTAS Studio AI uses cookies, local storage,
          and related tools. You can manage preferences via our site banner.
        </p>
        {COOKIE_SECTIONS.map((s) => (
          <section key={s.title} id={s.title.replace(/\s+/g, "-").toLowerCase()}>
            <h2>{s.title}</h2>
            <p>{s.body}</p>
          </section>
        ))}
      </div>
    </LegalLayout>
  );
}
