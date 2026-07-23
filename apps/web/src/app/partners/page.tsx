import type { Metadata } from "next";
import Link from "next/link";
import { COMPANY_NAME, PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";
import { PartnerApplicationForm } from "@/components/affiliate/PartnerApplicationForm";
import { buildPageMetadata } from "@/lib/site-metadata";
import { PARTNER_TYPES } from "@/lib/affiliate/config";

export const metadata: Metadata = buildPageMetadata({
  title: "Partners",
  description: `Partner with ${PRODUCT_NAME} — Creative & Marketing agencies, Software, Education, Technology, and Enterprise. Apply honestly; no invented partnerships.`,
  path: "/partners",
  openGraphTitle: `Partners · ${PRODUCT_NAME}`,
  openGraphDescription:
    "Explore partnership tracks with RTAS Digital Marketing Company. Applications are reviewed — we do not fabricate logos or partner counts.",
});

const PROCESS = [
  {
    step: "1",
    title: "Apply",
    body: "Submit the partnership form with your organization, track, and collaboration brief.",
  },
  {
    step: "2",
    title: "Review",
    body: "RTAS reviews ICP fit, brand safety, and Identity Preservation alignment. No auto-approval.",
  },
  {
    step: "3",
    title: "Agreement",
    body: "Accepted partners receive a written agreement before any public listing or co-marketing.",
  },
  {
    step: "4",
    title: "Enable",
    body: "Access the partner dashboard, resources center, and channel materials once approved.",
  },
] as const;

const REQUIREMENTS = [
  "Authorized-content only — no deepfake / unauthorized likeness positioning",
  "Honest pricing and feature claims (Tester $5 · Standard $89 · Premium $249)",
  "Willingness to disclose partnership relationship where required",
  "A named contact for commercial and brand review",
] as const;

export default function PartnersPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="text-center">
          <p className="rtas-eyebrow">Partners</p>
          <h1 className="text-zinc-100">Build with {COMPANY_NAME}</h1>
          <p className="mx-auto mt-3 max-w-2xl text-ds-text-muted">
            Partnership tracks for creative & marketing agencies, software, education, technology,
            and enterprise. We list open programs — not fabricated logos, revenue shares, or partner
            counts.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <ButtonLink href="#apply" variant="lavender">
              Apply to partner
            </ButtonLink>
            <ButtonLink href="/affiliate" variant="ghost">
              Affiliate program
            </ButtonLink>
            <ButtonLink href="/partners/resources" variant="ghost">
              Marketing resources
            </ButtonLink>
            <ButtonLink href="/partners/dashboard" variant="ghost">
              Partner dashboard
            </ButtonLink>
          </div>
        </InnerPageSection>

        <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-3" aria-labelledby="partner-tracks">
          <InnerPageSection className="md:col-span-2 lg:col-span-3 text-center pb-2">
            <h2 id="partner-tracks" className="text-xl text-zinc-100">
              Partnership tracks
            </h2>
          </InnerPageSection>
          {PARTNER_TYPES.map((t) => (
            <InnerPageSection key={t.id}>
              <h3 className="text-lg text-zinc-100">{t.title}</h3>
              <p className="mt-2 text-sm text-ds-text-muted">{t.body}</p>
            </InnerPageSection>
          ))}
        </section>

        <InnerPageSection aria-labelledby="partner-benefits">
          <h2 id="partner-benefits" className="text-xl text-zinc-100">
            Benefits
          </h2>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-ds-text-muted">
            <li>Early access to product roadmap conversations relevant to your track</li>
            <li>Co-marketing review (case studies only with written approval — none fabricated)</li>
            <li>Access to the Marketing Resources Center and brand guidelines</li>
            <li>
              Path to channel / reseller conversations for qualified enterprise partners (see
              channel sales docs)
            </li>
            <li>
              Separate{" "}
              <Link href="/affiliate" className="text-ds-accent-lavender underline-offset-2 hover:underline">
                affiliate track
              </Link>{" "}
              for creator/publisher referrals (payouts not live until configured)
            </li>
          </ul>
        </InnerPageSection>

        <InnerPageSection aria-labelledby="partner-requirements">
          <h2 id="partner-requirements" className="text-xl text-zinc-100">
            Requirements
          </h2>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-ds-text-muted">
            {REQUIREMENTS.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
        </InnerPageSection>

        <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-4" aria-labelledby="partner-process">
          <InnerPageSection className="md:col-span-2 lg:col-span-4 text-center pb-2">
            <h2 id="partner-process" className="text-xl text-zinc-100">
              Process
            </h2>
          </InnerPageSection>
          {PROCESS.map((p) => (
            <InnerPageSection key={p.step}>
              <p className="rtas-eyebrow">Step {p.step}</p>
              <h3 className="mt-1 text-lg text-zinc-100">{p.title}</h3>
              <p className="mt-2 text-sm text-ds-text-muted">{p.body}</p>
            </InnerPageSection>
          ))}
        </section>

        <InnerPageSection aria-labelledby="partner-resources">
          <h2 id="partner-resources" className="text-xl text-zinc-100">
            Resources
          </h2>
          <p className="mt-2 text-sm text-ds-text-muted">
            Logos, brand guidelines, screenshots, video links, banners, social kit, and email
            templates are organized in the{" "}
            <Link
              href="/partners/resources"
              className="text-ds-accent-lavender underline-offset-2 hover:underline"
            >
              Marketing Resources Center
            </Link>
            . Missing assets are labeled as placeholders — not invented downloads.
          </p>
          <div className="mt-4 flex flex-wrap gap-3">
            <ButtonLink href="/enterprise" variant="ghost">
              Enterprise sales
            </ButtonLink>
            <ButtonLink href="/about" variant="ghost">
              About RTAS
            </ButtonLink>
            <ButtonLink href="/developers" variant="ghost">
              Developers
            </ButtonLink>
          </div>
        </InnerPageSection>

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
            Applications are stored in the database and emailed to the RTAS team when Resend/SMTP is
            configured. Sign in first if you want status on your partner dashboard.
          </p>
          <div className="mt-6 max-w-xl">
            <PartnerApplicationForm />
          </div>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
