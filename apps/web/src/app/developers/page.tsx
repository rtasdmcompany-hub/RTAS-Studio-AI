import type { Metadata } from "next";
import { PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";

export const metadata: Metadata = {
  title: "Developers",
  description: `Developer resources for ${PRODUCT_NAME} — health checks, webhooks, sharing APIs, and integration notes.`,
};

const TOPICS = [
  {
    title: "Health & readiness",
    body: "Monitor service health via /api/health and readiness via /api/ready. Use these endpoints for uptime checks and deploy gates.",
    href: "/status",
  },
  {
    title: "Payments webhooks",
    body: "Paddle and Lemon Squeezy webhooks update subscription state server-side. Configure endpoints in your merchant dashboard to the published webhook routes.",
    href: "/help/billing",
  },
  {
    title: "Share links",
    body: "Generated videos can be published through the share API and public /share/[videoId] pages for social and client review.",
    href: "/showcase",
  },
  {
    title: "Source & issues",
    body: "The product monorepo and release notes live on GitHub. Prefer Help Center for account issues; use GitHub for engineering discussion.",
    href: "https://github.com/rtasdmcompany-hub/RTAS-Studio-AI",
  },
] as const;

export default function DevelopersPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="text-center">
          <p className="rtas-eyebrow">Developers</p>
          <h1 className="text-white">Build with {PRODUCT_NAME}</h1>
          <p className="mx-auto mt-3 max-w-2xl text-ds-text-muted">
            Integration notes for operators and engineers — health probes, billing webhooks, and
            share surfaces. Creator workflow docs stay under Documentation and How to use.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/status" variant="lavender">
              System status
            </ButtonLink>
            <ButtonLink href="/docs" variant="ghost">
              Product docs
            </ButtonLink>
          </div>
        </InnerPageSection>

        <section className="grid gap-4 md:grid-cols-2" aria-label="Developer topics">
          {TOPICS.map((item) => (
            <InnerPageSection key={item.title}>
              <h2 className="text-lg text-white">{item.title}</h2>
              <p className="mt-2 text-sm text-ds-text-muted">{item.body}</p>
              <div className="mt-4">
                {item.href.startsWith("http") ? (
                  <a
                    href={item.href}
                    className="rtas-btn-ghost rtas-ui-btn"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Open →
                  </a>
                ) : (
                  <ButtonLink href={item.href} variant="ghost">
                    Open →
                  </ButtonLink>
                )}
              </div>
            </InnerPageSection>
          ))}
        </section>

        <InnerPageSection className="text-center">
          <h2 className="text-xl text-white">Support vs engineering</h2>
          <p className="mx-auto mt-2 max-w-xl text-sm text-ds-text-muted">
            Account, credits, and download questions go to Help Center. Platform status and API
            surfaces are documented here for technical teams.
          </p>
          <div className="mt-5 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/help" variant="lavender">
              Help Center
            </ButtonLink>
            <ButtonLink href="/help/contact" variant="ghost">
              Contact
            </ButtonLink>
          </div>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
