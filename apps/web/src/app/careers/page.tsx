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
  description: `Careers at ${COMPANY_NAME} — open roles, benefits, and how to apply to help build ${PRODUCT_NAME}.`,
  openGraph: {
    title: `Careers · ${PRODUCT_NAME}`,
    description:
      "Join the team building an international AI video studio — product, engineering, and creator success.",
  },
};

const OPEN_ROLES = [
  {
    title: "Product designer (Studio & marketing)",
    type: "Rolling applications",
    location: "Remote-friendly · international",
    body: "Shape the Studio wizard, conversion surfaces, and international UX for creators shipping music videos, ads, and stories. You will partner with engineering on clarity, accessibility, and premium motion.",
  },
  {
    title: "Full-stack engineer",
    type: "Rolling applications",
    location: "Remote-friendly · international",
    body: "Own Next.js app routes, BFF APIs, credit guards, and cloud GPU pipeline integrations. We value reliability, typed contracts, and honest error surfaces over flashy demos.",
  },
  {
    title: "Creator success specialist",
    type: "Rolling applications",
    location: "Remote-friendly · international",
    body: "Help artists and brands go from first render to commercial export. You will improve guides, triage support, and turn real creator friction into product feedback.",
  },
  {
    title: "Growth & partnerships",
    type: "Rolling applications",
    location: "Remote-friendly · international",
    body: "Build creator and agency relationships, refine packaging for international markets, and keep pricing messaging aligned with what creators actually ship.",
  },
] as const;

const BENEFITS = [
  {
    title: "Remote-first craft",
    body: "Work where you do your best thinking. We coordinate asynchronously across time zones with clear written decisions.",
  },
  {
    title: "Product ownership",
    body: "Small teams, real scope. You will see your work in Studio, billing, and help surfaces used by international creators.",
  },
  {
    title: "Learning budget",
    body: "Support for tools, courses, and conferences that improve your craft in AI product, design, or creative production.",
  },
  {
    title: "Transparent culture",
    body: "We hire for honesty in billing and product quality — the same standards we publish to customers.",
  },
] as const;

const CAREERS_MAIL = `mailto:${SITE_SUPPORT_EMAIL}?subject=${encodeURIComponent("Careers — RTAS Studio AI")}`;

export default function CareersPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="text-center">
          <p className="rtas-eyebrow">Careers</p>
          <h1 className="text-white">Build cinema with AI</h1>
          <p className="mx-auto mt-3 max-w-2xl text-ds-text-muted">
            {COMPANY_NAME} is growing {PRODUCT_NAME} for international creators and teams.
            We hire for craft, honesty in billing, and product quality — not vanity metrics.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <ButtonLink href={CAREERS_MAIL} variant="lavender">
              Apply by email
            </ButtonLink>
            <ButtonLink href="/about" variant="ghost">
              About RTAS
            </ButtonLink>
          </div>
        </InnerPageSection>

        <section aria-labelledby="careers-roles">
          <InnerPageSection className="text-center pb-2">
            <h2 id="careers-roles" className="text-xl text-white">
              Open roles
            </h2>
            <p className="mx-auto mt-2 max-w-xl text-sm text-ds-text-muted">
              We accept rolling applications year-round. Strong matches move into interviews
              when a seat opens; everyone who applies receives a reply.
            </p>
          </InnerPageSection>
          <div className="grid gap-4 md:grid-cols-2">
            {OPEN_ROLES.map((role) => (
              <InnerPageSection key={role.title}>
                <p className="rtas-eyebrow">{role.type}</p>
                <h3 className="text-lg text-white">{role.title}</h3>
                <p className="mt-1 text-xs text-ds-text-muted">{role.location}</p>
                <p className="mt-2 text-sm text-ds-text-muted">{role.body}</p>
              </InnerPageSection>
            ))}
          </div>
        </section>

        <section aria-labelledby="careers-benefits">
          <InnerPageSection className="text-center pb-2">
            <h2 id="careers-benefits" className="text-xl text-white">
              Benefits & working style
            </h2>
          </InnerPageSection>
          <div className="grid gap-4 md:grid-cols-2">
            {BENEFITS.map((item) => (
              <InnerPageSection key={item.title}>
                <h3 className="text-lg text-white">{item.title}</h3>
                <p className="mt-2 text-sm text-ds-text-muted">{item.body}</p>
              </InnerPageSection>
            ))}
          </div>
        </section>

        <InnerPageSection className="text-center">
          <h2 className="text-xl text-white">How to apply</h2>
          <ol className="mx-auto mt-4 max-w-xl space-y-3 text-left text-sm text-ds-text-muted">
            <li>
              <strong className="text-zinc-100">1. Choose a role</strong> — pick the open role
              that best matches your experience, or note a related specialty.
            </li>
            <li>
              <strong className="text-zinc-100">2. Send a short note</strong> — include relevant
              work (portfolio, GitHub, or case study), where you are based, and preferred
              working hours.
            </li>
            <li>
              <strong className="text-zinc-100">3. Email us</strong> — write to{" "}
              <a href={CAREERS_MAIL}>{SITE_SUPPORT_EMAIL}</a> with subject line “Careers”.
              We reply when we review your application.
            </li>
          </ol>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <ButtonLink href={CAREERS_MAIL} variant="lavender">
              Email careers
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
