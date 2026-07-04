import type { LegalSection } from "@rtas/shared";

type Props = {
  intro: string;
  sections: readonly LegalSection[];
};

export function LegalProse({ intro, sections }: Props) {
  return (
    <div className="legal-prose-shell">
      <article className="prose prose-invert max-w-4xl text-left leading-relaxed text-zinc-300 legal-prose">
        <p className="legal-lead !text-zinc-300">{intro}</p>
        {sections.map((section) => (
          <section key={section.title} aria-labelledby={slugId(section.title)}>
            <h3 id={slugId(section.title)}>{section.title}</h3>
            <p>{section.body}</p>
            {section.bullets && section.bullets.length > 0 ? (
              <ul>
                {section.bullets.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            ) : null}
          </section>
        ))}
      </article>
    </div>
  );
}

function slugId(title: string): string {
  return title.replace(/[^\w]+/g, "-").replace(/^-|-$/g, "").toLowerCase();
}
