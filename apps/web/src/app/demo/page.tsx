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
  description: `Request a live demo of ${PRODUCT_NAME} for your team — Identity Preservation, credits, and production workflows. Validated form notifies sales when email delivery is configured.`,
  path: "/demo",
  openGraphTitle: `Schedule a Demo · ${PRODUCT_NAME}`,
  openGraphDescription:
    "Book a product demo with RTAS. No fake calendars or invented availability — we reply to real business emails.",
});

const WHAT_TO_EXPECT = [
  {
    title: "30–45 minute walkthrough",
    body: "Studio compose → render → export, credits (1 credit = 1 second), and Identity Preservation policy.",
  },
  {
    title: "Your use case first",
    body: "Bring a real brief when you can — music video, ad, brand film, or education content.",
  },
  {
    title: "Honest next steps",
    body: "Self-serve Tester/Standard/Premium or a proposal when volume or procurement requires it. No invented discounts.",
  },
] as const;

export default function DemoRequestPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="text-center">
          <p className="rtas-eyebrow">Demo request</p>
          <h1 className="text-zinc-100">See {PRODUCT_NAME} with your team</h1>
          <p className="mx-auto mt-3 max-w-2xl text-ds-text-muted">
            Submit a demo request with a business email. We notify the commercial inbox when
            delivery is configured; otherwise you will see an honest error and can email{" "}
            {SITE_SUPPORT_EMAIL} directly.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <ButtonLink href="#request" variant="lavender">
              Request demo
            </ButtonLink>
            <ButtonLink href="/enterprise" variant="ghost">
              Enterprise overview
            </ButtonLink>
            <ButtonLink href="/pricing" variant="ghost">
              Pricing
            </ButtonLink>
          </div>
        </InnerPageSection>

        <section className="grid gap-4 md:grid-cols-3" aria-labelledby="demo-expect">
          <InnerPageSection className="md:col-span-3 text-center pb-2">
            <h2 id="demo-expect" className="text-xl text-zinc-100">
              What to expect
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
            Schedule a demo
          </h2>
          <p className="mt-2 max-w-xl text-sm text-ds-text-muted">
            Prefer a quote or broader enterprise inquiry? Use the{" "}
            <Link href="/enterprise#contact" className="text-ds-accent-lavender hover:underline">
              enterprise contact form
            </Link>
            .
          </p>
          <div className="mt-6 max-w-xl">
            <CommercialLeadForm
              kind="enterprise"
              submitLabel="Send demo request"
              showCompany
              showRole
              showRequestType
              defaultRequestType="demo"
              emailLabel="Business email"
              messageLabel="Demo context"
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
