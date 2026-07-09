import { PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";

const WORKFLOW_STEPS = [
  {
    id: "compose",
    step: "01",
    title: "Compose",
    body: "Pick category, drop lyrics, audio, and face lock — one guided wizard, zero clutter.",
  },
  {
    id: "render",
    step: "02",
    title: "Render",
    body: "Cinematic AI pipeline with identity-locked faces, clear credit cost, and live progress.",
  },
  {
    id: "publish",
    step: "03",
    title: "Publish",
    body: "Preview full-screen, download your master, and revisit every render in your library.",
  },
] as const;

export default function AboutPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="rtas-about-page text-center">
          <p className="rtas-eyebrow">How it works</p>
          <h1 className="text-zinc-100">One studio. Three beats.</h1>
          <p className="rtas-about-page__lead">
            From first lyric to final export — {PRODUCT_NAME} keeps compose, render,
            and publish in a single cinematic workspace built for global creators.
          </p>

          <div className="rtas-about-page__pipeline">
            {WORKFLOW_STEPS.map((step) => (
              <article key={step.id} className="rtas-pipeline-step">
                <span className="rtas-pipeline-step__num">{step.step}</span>
                <h3 className="text-zinc-100">{step.title}</h3>
                <p>{step.body}</p>
              </article>
            ))}
          </div>

          <div className="rtas-about-page__actions">
            <ButtonLink href="/studio" variant="lavender">
              Open Studio <span aria-hidden>→</span>
            </ButtonLink>
            <ButtonLink href="/pricing" variant="ghost">
              View pricing
            </ButtonLink>
          </div>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
