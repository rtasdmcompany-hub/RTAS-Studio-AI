import type { Metadata } from "next";
import Link from "next/link";
import {
  PREMIUM_PRICE_USD,
  PRODUCT_NAME,
  STANDARD_PRICE_USD,
  TESTER_PRICE_USD,
} from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";
import { CommercialLeadForm } from "@/components/commercial/CommercialLeadForm";
import { buildPageMetadata } from "@/lib/site-metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Enterprise",
  description: `Enterprise sales for ${PRODUCT_NAME} — security posture, deployment options, Production Enterprise pricing ($${PREMIUM_PRICE_USD}/mo), and request demo, proposal, or meeting.`,
  path: "/enterprise",
  openGraphTitle: `Enterprise · ${PRODUCT_NAME}`,
  openGraphDescription:
    "Talk to RTAS about team workflows, Identity Preservation policy, and Production Enterprise capacity. No invented client logos or case studies.",
});

const BENEFITS = [
  {
    title: "Cinematic Production Enterprise",
    body: `Premium plan at $${PREMIUM_PRICE_USD}/mo with 2000 seconds and cinematic 4K capacity for brand and music work.`,
  },
  {
    title: "Transparent credit economics",
    body: "1 credit = 1 second. No vague “unlimited AI” packaging — teams can forecast cost from output length.",
  },
  {
    title: "Authorized Identity Preservation",
    body: "Likeness workflows are intentional and policy-bound. Unauthorized identity use is not supported.",
  },
  {
    title: "Operational visibility",
    body: "Health/readiness probes, status page, and documented support channels for production teams.",
  },
] as const;

const SECURITY = [
  "TLS in transit; secrets stay server-side (never in the browser).",
  "Fail-closed payment webhooks and rate limits on sensitive API paths.",
  "Email-verified sessions for API access; admin surfaces are noindexed and secret-gated.",
  "We do not claim SOC 2 / ISO certification unless independently attested — ask us for the current posture.",
] as const;

const DEPLOYMENT = [
  {
    title: "SaaS (default)",
    body: "Hosted at rtasstudio.com — fastest path for most teams. Merchant-of-Record checkout via Paddle.",
  },
  {
    title: "Guided onboarding",
    body: "Demo → proposal → kickoff for brand/agency workflows. Custom SLAs and dedicated infrastructure are discussed case-by-case — not advertised as shipped features.",
  },
  {
    title: "Self-serve evaluation",
    body: `Start with Tester ($${TESTER_PRICE_USD}) or Standard ($${STANDARD_PRICE_USD}/mo) while enterprise scoping runs in parallel.`,
  },
] as const;

export default function EnterprisePage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="text-center">
          <p className="rtas-eyebrow">Enterprise</p>
          <h1 className="text-zinc-100">Studio capacity for brands & teams</h1>
          <p className="mx-auto mt-3 max-w-2xl text-ds-text-muted">
            {PRODUCT_NAME} for agencies and production teams that need Identity Preservation,
            clear credits, and commercial downloads — without invented client logos or fake case
            studies.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/demo" variant="lavender">
              Schedule demo
            </ButtonLink>
            <ButtonLink href="#contact" variant="ghost">
              Enterprise inquiry
            </ButtonLink>
            <ButtonLink href="/pricing" variant="ghost">
              Compare plans
            </ButtonLink>
            <ButtonLink href="/beta" variant="ghost">
              Public beta
            </ButtonLink>
          </div>
        </InnerPageSection>

        <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-4" aria-labelledby="ent-paths">
          <InnerPageSection className="lg:col-span-4 text-center pb-2">
            <h2 id="ent-paths" className="text-xl text-zinc-100">
              How to engage sales
            </h2>
          </InnerPageSection>
          {[
            {
              title: "Schedule demo",
              body: "Live product walkthrough for your team.",
              href: "/demo",
              cta: "Open demo form",
            },
            {
              title: "Enterprise inquiry",
              body: "Security, deployment, and team workflow questions.",
              href: "#contact",
              cta: "Start inquiry",
            },
            {
              title: "Request quote",
              body: "Volume or procurement — select Quote on the form below.",
              href: "#contact",
              cta: "Request quote",
            },
            {
              title: "Sales contact",
              body: "Email contact@rtasstudio.com with your business domain.",
              href: "mailto:contact@rtasstudio.com",
              cta: "Email sales",
            },
          ].map((item) => (
            <InnerPageSection key={item.title}>
              <h3 className="text-lg text-zinc-100">{item.title}</h3>
              <p className="mt-2 text-sm text-ds-text-muted">{item.body}</p>
              <div className="mt-4">
                {item.href.startsWith("mailto:") ? (
                  <a href={item.href} className="rtas-btn-ghost rtas-ui-btn">
                    {item.cta} →
                  </a>
                ) : (
                  <ButtonLink href={item.href} variant="ghost">
                    {item.cta} →
                  </ButtonLink>
                )}
              </div>
            </InnerPageSection>
          ))}
        </section>

        <section className="grid gap-4 md:grid-cols-2" aria-labelledby="ent-benefits">
          <InnerPageSection className="md:col-span-2 text-center pb-2">
            <h2 id="ent-benefits" className="text-xl text-zinc-100">
              Benefits
            </h2>
          </InnerPageSection>
          {BENEFITS.map((b) => (
            <InnerPageSection key={b.title}>
              <h3 className="text-lg text-zinc-100">{b.title}</h3>
              <p className="mt-2 text-sm text-ds-text-muted">{b.body}</p>
            </InnerPageSection>
          ))}
        </section>

        <InnerPageSection aria-labelledby="ent-security">
          <h2 id="ent-security" className="text-xl text-zinc-100">
            Security posture
          </h2>
          <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-ds-text-muted">
            {SECURITY.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <p className="mt-4 text-sm">
            <Link href="/trust-safety" className="text-ds-accent-lavender hover:underline">
              Trust & Safety
            </Link>
            {" · "}
            <Link href="/privacy" className="text-ds-accent-lavender hover:underline">
              Privacy Policy
            </Link>
          </p>
        </InnerPageSection>

        <section className="grid gap-4 md:grid-cols-3" aria-labelledby="ent-deploy">
          <InnerPageSection className="md:col-span-3 text-center pb-2">
            <h2 id="ent-deploy" className="text-xl text-zinc-100">
              Deployment options
            </h2>
          </InnerPageSection>
          {DEPLOYMENT.map((d) => (
            <InnerPageSection key={d.title}>
              <h3 className="text-lg text-zinc-100">{d.title}</h3>
              <p className="mt-2 text-sm text-ds-text-muted">{d.body}</p>
            </InnerPageSection>
          ))}
        </section>

        <InnerPageSection aria-labelledby="ent-pricing" className="text-center">
          <h2 id="ent-pricing" className="text-xl text-zinc-100">
            Pricing contact
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-sm text-ds-text-muted">
            Published list: Tester ${TESTER_PRICE_USD} · Standard ${STANDARD_PRICE_USD}/mo ·
            Premium ${PREMIUM_PRICE_USD}/mo. Volume, procurement, and custom commercial terms are
            handled via proposal — we do not invent discount schedules in public copy.
          </p>
          <div className="mt-5">
            <ButtonLink href="/pricing" variant="ghost">
              Open pricing page →
            </ButtonLink>
          </div>
        </InnerPageSection>

        <InnerPageSection id="contact" aria-labelledby="ent-contact">
          <h2 id="ent-contact" className="text-xl text-zinc-100">
            Enterprise inquiry, demo, quote, or meeting
          </h2>
          <p className="mt-2 max-w-xl text-sm text-ds-text-muted">
            Use a business email. Submissions notify the RTAS commercial inbox when email delivery
            is configured; otherwise you get an honest error and can write to contact@rtasstudio.com.
          </p>
          <div className="mt-6 max-w-xl">
            <CommercialLeadForm
              kind="enterprise"
              submitLabel="Send enterprise request"
              showCompany
              showRole
              showRequestType
              emailLabel="Business email"
              messageLabel="Project context"
              messagePlaceholder="Team size, markets, Identity Preservation needs, timeline…"
            />
          </div>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
