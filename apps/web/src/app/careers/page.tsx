import type { Metadata } from "next";
import { COMPANY_NAME, PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";
import { SITE_SUPPORT_EMAIL } from "@/lib/site-links";

export const metadata: Metadata = {
  title: "Careers",
  description: `Careers at ${COMPANY_NAME} — help build ${PRODUCT_NAME}, the international AI video studio.`,
};

const ROLES = [
  {
    title: "Product & design",
    body: "Shape the Studio wizard, marketing conversion, and international UX for creators shipping music videos, ads, and stories.",
  },
  {
    title: "Full-stack engineering",
    body: "Next.js, APIs, credit guards, and cloud GPU pipelines — reliability and clarity over hype.",
  },
  {
    title: "Creator success",
    body: "Help artists and brands go from first render to commercial export with clear guides and support.",
  },
] as const;

export default function CareersPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="text-center">
          <p className="rtas-eyebrow">Careers</p>
          <h1 className="text-white">Build cinema with AI</h1>
          <p className="mx-auto mt-3 max-w-2xl text-ds-text-muted">
            {COMPANY_NAME} is growing {PRODUCT_NAME} for international creators and teams. We hire
            for craft, honesty in billing, and product quality — not vanity metrics.
          </p>
        </InnerPageSection>

        <section className="grid gap-4 md:grid-cols-3" aria-label="Open interest areas">
          {ROLES.map((role) => (
            <InnerPageSection key={role.title} className="text-center">
              <h2 className="text-lg text-white">{role.title}</h2>
              <p className="mt-2 text-sm text-ds-text-muted">{role.body}</p>
            </InnerPageSection>
          ))}
        </section>

        <InnerPageSection className="text-center">
          <h2 className="text-xl text-white">How to apply</h2>
          <p className="mx-auto mt-2 max-w-xl text-sm text-ds-text-muted">
            Send a short note about the role you want, relevant work, and where you are based. We
            reply when a match is open.
          </p>
          <p className="mt-3 text-sm text-ds-text-muted">
            Email{" "}
            <a href={`mailto:${SITE_SUPPORT_EMAIL}?subject=${encodeURIComponent("Careers — RTAS Studio AI")}`}>
              {SITE_SUPPORT_EMAIL}
            </a>{" "}
            with subject line “Careers”.
          </p>
          <div className="mt-5 flex flex-wrap justify-center gap-3">
            <ButtonLink href={`mailto:${SITE_SUPPORT_EMAIL}?subject=Careers%20%E2%80%94%20RTAS%20Studio%20AI`} variant="lavender">
              Email careers
            </ButtonLink>
            <ButtonLink href="/about" variant="ghost">
              About RTAS
            </ButtonLink>
          </div>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
