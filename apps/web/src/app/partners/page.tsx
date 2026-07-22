import type { Metadata } from "next";
import { COMPANY_NAME, PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";
import { CommercialLeadForm } from "@/components/commercial/CommercialLeadForm";
import { buildPageMetadata } from "@/lib/site-metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Partners",
  description: `Partner with ${PRODUCT_NAME} — Technology, Creative Agencies, Enterprise, Affiliate, and Education programs. Apply honestly; no invented partnerships.`,
  path: "/partners",
  openGraphTitle: `Partners · ${PRODUCT_NAME}`,
  openGraphDescription:
    "Explore partnership tracks with RTAS Digital Marketing Company. Applications are reviewed — we do not fabricate logos or partner counts.",
});

const TRACKS = [
  {
    id: "technology",
    title: "Technology",
    body: "Integrations, tooling, and platform collaborations that extend Studio workflows without overclaiming a public marketplace.",
  },
  {
    id: "creative_agencies",
    title: "Creative Agencies",
    body: "Agencies shipping music videos, ads, and brand films who want guided Studio capacity and clear commercial licensing.",
  },
  {
    id: "enterprise",
    title: "Enterprise",
    body: "Larger organizations exploring Production Enterprise packaging, procurement, and Identity Preservation policy alignment.",
  },
  {
    id: "affiliate",
    title: "Affiliate",
    body: "Creator and educator affiliates who want to refer paid plans. Program economics are confirmed in writing — not invented publicly.",
  },
  {
    id: "education",
    title: "Education",
    body: "Schools, labs, and training programs evaluating Studio for coursework with authorized content only.",
  },
] as const;

export default function PartnersPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="text-center">
          <p className="rtas-eyebrow">Partners</p>
          <h1 className="text-zinc-100">Build with {COMPANY_NAME}</h1>
          <p className="mx-auto mt-3 max-w-2xl text-ds-text-muted">
            Partnership tracks for technology, agencies, enterprise, affiliates, and education.
            We list open programs — not fabricated logos, revenue shares, or partner counts.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <ButtonLink href="#apply" variant="lavender">
              Apply to partner
            </ButtonLink>
            <ButtonLink href="/enterprise" variant="ghost">
              Enterprise sales
            </ButtonLink>
            <ButtonLink href="/about" variant="ghost">
              About RTAS
            </ButtonLink>
          </div>
        </InnerPageSection>

        <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-3" aria-labelledby="partner-tracks">
          <InnerPageSection className="md:col-span-2 lg:col-span-3 text-center pb-2">
            <h2 id="partner-tracks" className="text-xl text-zinc-100">
              Partnership tracks
            </h2>
          </InnerPageSection>
          {TRACKS.map((t) => (
            <InnerPageSection key={t.id}>
              <h3 className="text-lg text-zinc-100">{t.title}</h3>
              <p className="mt-2 text-sm text-ds-text-muted">{t.body}</p>
            </InnerPageSection>
          ))}
        </section>

        <InnerPageSection className="text-center">
          <h2 className="text-xl text-zinc-100">Integrity note</h2>
          <p className="mx-auto mt-2 max-w-xl text-sm text-ds-text-muted">
            Accepted partners will be listed only after a signed agreement. Until then, this page
            remains an application surface — not a fake logo wall.
          </p>
        </InnerPageSection>

        <InnerPageSection id="apply" aria-labelledby="partner-apply">
          <h2 id="partner-apply" className="text-xl text-zinc-100">
            Partnership application
          </h2>
          <p className="mt-2 max-w-xl text-sm text-ds-text-muted">
            Your application emails the RTAS team when Resend/SMTP is configured. If delivery is
            unavailable, the API returns an honest failure and you can write to
            contact@rtasstudio.com.
          </p>
          <div className="mt-6 max-w-xl">
            <CommercialLeadForm
              kind="partners"
              submitLabel="Submit partnership application"
              showCompany
              showRole
              showWebsite
              showPartnerType
              messageRequired
              messageMinLength={20}
              messageLabel="Partnership opportunity"
              messagePlaceholder="Describe the collaboration, audience, and what success looks like…"
            />
          </div>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
