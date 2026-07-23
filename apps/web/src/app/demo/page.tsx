import type { Metadata } from "next";
import Link from "next/link";
import { PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";
import { CommercialLeadForm } from "@/components/commercial/CommercialLeadForm";
import { buildPageMetadata } from "@/lib/site-metadata";
import { SITE_SUPPORT_EMAIL } from "@/lib/site-links";

export const metadata: Metadata = buildPageMetadata({
  title: "Schedule a Demo",
  description: `Book a demo, technical consultation, or discovery call for ${PRODUCT_NAME}. Validated form notifies sales and confirms when email delivery is configured.`,
  path: "/demo",
  openGraphTitle: `Schedule a Demo · ${PRODUCT_NAME}`,
  openGraphDescription:
    "Book a product demo, technical consultation, or discovery call with RTAS. No fake calendars or invented availability.",
});

const WHAT_TO_EXPECT = [
  {
    title: "Book Demo",
    body: "30–45 minute studio walkthrough: compose → render → export, credits, Identity Preservation.",
  },
  {
    title: "Technical Consultation",
    body: "API, security posture, deployment options, and integration scoping for technical buyers.",
  },
  {
    title: "Discovery Call",
    body: "Use-case and commercial discovery for agencies and brand teams before a proposal.",
  },
] as const;

export default function DemoRequestPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="text-center">
          <p className="rtas-eyebrow">Demo booking</p>
          <h1 className="text-zinc-100">See {PRODUCT_NAME} with your team</h1>
          <p className="mx-auto mt-3 max-w-2xl text-ds-text-muted">
            Choose Book Demo, Technical Consultation, or Discovery Call. We notify the commercial
            inbox and send a confirmation when email delivery is configured; otherwise you will see
            an honest error and can email {SITE_SUPPORT_EMAIL} directly.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <ButtonLink href="#request" variant="lavender">
              Book a session
            </ButtonLink>
            <ButtonLink href="/enterprise" variant="ghost">
              Enterprise overview
            </ButtonLink>
            <ButtonLink href="/enterprise#pricing" variant="ghost">
              Enterprise pricing
            </ButtonLink>
          </div>
        </InnerPageSection>

        <section className="grid gap-4 md:grid-cols-3" aria-labelledby="demo-expect">
          <InnerPageSection className="md:col-span-3 text-center pb-2">
            <h2 id="demo-expect" className="text-xl text-zinc-100">
              Session types
            </h2>
          </InnerPageSection>
          {WHAT_TO_EXPECT.map((item) => (
            <InnerPageSection key={item.title}>
              <h3 className="text-lg text-zinc-100">{item.title}</h3>
              <p className="mt-2 text-sm text-ds-text-muted">{item.body}</p>
            </InnerPageSection>
          ))}
        </section>

        <InnerPageSection id="request" aria-labelledby="demo-form">
          <h2 id="demo-form" className="text-xl text-zinc-100">
            Book Demo / Technical Consultation / Discovery Call
          </h2>
          <p className="mt-2 max-w-xl text-sm text-ds-text-muted">
            Prefer a written proposal? Use the{" "}
            <Link href="/enterprise#contact" className="text-ds-accent-lavender hover:underline">
              enterprise contact form
            </Link>
            .
          </p>
          <div className="mt-6 max-w-xl">
            <CommercialLeadForm
              kind="demo"
              submitLabel="Confirm booking request"
              showCompany
              showRole
              showWebsite
              showEnterpriseFields
              showDemoType
              showPlanInterest
              defaultDemoType="book_demo"
              defaultRequestType="demo"
              emailLabel="Business email"
              messageLabel="Session context"
              messagePlaceholder="Team size, markets, Identity Preservation needs, preferred timezone…"
              messageRequired
              messageMinLength={20}
            />
          </div>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
