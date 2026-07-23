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
import { EnterpriseCapabilityGrid } from "@/components/enterprise/EnterpriseCapabilityGrid";
import { EnterprisePricingSection } from "@/components/enterprise/EnterprisePricingSection";
import { EnterpriseTrustPanel } from "@/components/enterprise/EnterpriseTrustPanel";
import { PromotionPlacement } from "@/components/promotions/PromotionPlacement";
import { buildPageMetadata } from "@/lib/site-metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Enterprise",
  description: `Enterprise sales for ${PRODUCT_NAME} — private deployment scoping, security posture, Creator/Business mapping to Standard/Premium, and Contact Sales for Enterprise (no fixed price).`,
  path: "/enterprise",
  openGraphTitle: `Enterprise · ${PRODUCT_NAME}`,
  openGraphDescription:
    "Talk to RTAS about team workflows, Identity Preservation policy, and enterprise scoping. No invented client logos or case studies.",
});

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
            studies. Enterprise commercial terms are proposal-based; we do not publish a fixed
            Enterprise price.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/demo" variant="lavender">
              Book Demo
            </ButtonLink>
            <ButtonLink href="#contact" variant="ghost">
              Contact Sales
            </ButtonLink>
            <ButtonLink href="#pricing" variant="ghost">
              Enterprise pricing
            </ButtonLink>
            <ButtonLink href="/pricing" variant="ghost">
              Self-serve plans
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
              title: "Book Demo",
              body: "Product walkthrough, technical consultation, or discovery call.",
              href: "/demo",
              cta: "Open demo form",
            },
            {
              title: "Request Proposal",
              body: "Volume, procurement, or custom commercial terms.",
              href: "#contact",
              cta: "Start inquiry",
            },
            {
              title: "Contact Sales",
              body: "Security, deployment, and team workflow questions.",
              href: "#contact",
              cta: "Enterprise inquiry",
            },
            {
              title: "Email",
              body: "Write contact@rtasstudio.com with your business domain.",
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

        <EnterpriseCapabilityGrid />

        <InnerPageSection>
          <EnterpriseTrustPanel />
        </InnerPageSection>

        <section id="pricing">
          <EnterprisePricingSection />
        </section>

        <InnerPageSection className="text-center">
          <h2 className="text-xl text-zinc-100">Published list prices</h2>
          <p className="mx-auto mt-3 max-w-xl text-sm text-ds-text-muted">
            Tester ${TESTER_PRICE_USD} · Standard (Creator) ${STANDARD_PRICE_USD}/mo · Premium
            (Business) ${PREMIUM_PRICE_USD}/mo. Enterprise = Contact Sales / Request Proposal / Book
            Demo — never a fabricated SKU price.
          </p>
        </InnerPageSection>

        <PromotionPlacement
          placement="enterprise_cta"
          pagePath="/enterprise"
          title="Enterprise recommendations"
          emptyMinHeightClassName="min-h-[14rem]"
        />

        <InnerPageSection id="contact" aria-labelledby="ent-contact">
          <h2 id="ent-contact" className="text-xl text-zinc-100">
            Enterprise inquiry
          </h2>
          <p className="mt-2 max-w-xl text-sm text-ds-text-muted">
            Use a business email. Submissions are stored in the RTAS enterprise CRM when the database
            is configured, and notify the commercial inbox when email delivery is configured.
          </p>
          <div className="mt-6 max-w-xl">
            <CommercialLeadForm
              kind="enterprise"
              submitLabel="Send enterprise request"
              showCompany
              showRole
              showWebsite
              showRequestType
              showEnterpriseFields
              showPlanInterest
              defaultRequestType="inquiry"
              emailLabel="Business email"
              messageLabel="Project requirements"
              messagePlaceholder="Team size, markets, Identity Preservation needs, deployment questions, timeline…"
              messageRequired
              messageMinLength={20}
            />
          </div>
          <p className="mt-4 text-sm text-ds-text-muted">
            Prefer a live session?{" "}
            <Link href="/demo" className="text-ds-accent-lavender hover:underline">
              Book a demo
            </Link>
            .
          </p>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
