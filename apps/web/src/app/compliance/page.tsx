import type { Metadata } from "next";
import Link from "next/link";
import { PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";
import { StructuredData } from "@/components/seo/StructuredData";
import { buildPageMetadata } from "@/lib/site-metadata";
import { breadcrumbSchema } from "@/lib/structured-data";
import { SITE_PRIVACY_EMAIL, SITE_LEGAL_EMAIL } from "@/lib/site-links";

export const metadata: Metadata = buildPageMetadata({
  title: "Compliance Center",
  description: `GDPR/CCPA readiness, privacy controls, and security practices for ${PRODUCT_NAME}. Implemented vs Roadmap only — not a certification claim.`,
  path: "/compliance",
  openGraphTitle: `Compliance Center · ${PRODUCT_NAME}`,
  openGraphDescription:
    "Honest compliance posture: legal policies, privacy controls, encryption — no fabricated SOC/ISO stamps.",
});

type Row = {
  title: string;
  body: string;
  status: "Implemented" | "Partial" | "Roadmap";
  href?: string;
};

const ROWS: Row[] = [
  {
    title: "Legal policy suite",
    body: "Terms, Privacy, Cookies, Refund, AI Usage, Trust & Safety, Community Guidelines, Copyright & DMCA.",
    status: "Implemented",
    href: "/terms",
  },
  {
    title: "Cookie consent (Necessary / Analytics / Marketing)",
    body: "Banner + preference center; optional trackers gated before load.",
    status: "Implemented",
    href: "/cookies",
  },
  {
    title: "Self-serve data export & deletion request",
    body: "Signed-in Privacy settings: JSON export and deletion ticket workflow.",
    status: "Implemented",
    href: "/profile/privacy",
  },
  {
    title: "GDPR / CCPA readiness",
    body: "Policy disclosures, rights language, and operational workflows. Not a formal certification or supervisory approval.",
    status: "Partial",
    href: "/privacy",
  },
  {
    title: "Encryption in transit (TLS)",
    body: "Web and API traffic over TLS; secrets remain server-side.",
    status: "Implemented",
    href: "/security",
  },
  {
    title: "Data storage & subprocessors",
    body: "Account and studio data in configured cloud database/storage; payments via Paddle MoR; AI inference via configured providers.",
    status: "Implemented",
    href: "/privacy",
  },
  {
    title: "Privacy controls (email + cookies)",
    body: "Notification preferences and cookie category controls in-product.",
    status: "Implemented",
    href: "/profile/notifications",
  },
  {
    title: "Customer DPA template",
    body: "Enterprise DPA pack for countersignature — not published as self-serve.",
    status: "Roadmap",
  },
  {
    title: "SOC 2 Type I/II",
    body: "Attestation not obtained. Do not display SOC badges.",
    status: "Roadmap",
  },
  {
    title: "ISO 27001",
    body: "ISMS certification not obtained.",
    status: "Roadmap",
  },
];

const STATUS_CLASS: Record<Row["status"], string> = {
  Implemented: "border-emerald-500/40 text-emerald-300",
  Partial: "border-sky-500/40 text-sky-200",
  Roadmap: "border-amber-500/40 text-amber-200",
};

export default function ComplianceCenterPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <StructuredData
          data={breadcrumbSchema([
            { name: "Home", path: "/" },
            { name: "Compliance Center", path: "/compliance" },
          ])}
        />
        <InnerPageSection className="text-center">
          <p className="rtas-eyebrow">Trust</p>
          <h1 className="text-white">Compliance Center</h1>
          <p className="mx-auto mt-3 max-w-2xl text-ds-text-muted">
            Framework readiness for {PRODUCT_NAME} — what ships today versus what remains on
            the roadmap. We align practices with GDPR/CCPA expectations where applicable;
            we do not claim to be “GDPR certified,” SOC 2 certified, or ISO certified.
          </p>
        </InnerPageSection>

        <section className="grid gap-4" aria-labelledby="comp-matrix">
          <h2 id="comp-matrix" className="sr-only">
            Compliance matrix
          </h2>
          {ROWS.map((row) => (
            <InnerPageSection key={row.title}>
              <div className="flex flex-wrap items-start justify-between gap-2">
                <h3 className="text-lg text-white">{row.title}</h3>
                <span
                  className={`rounded-md border px-2 py-0.5 text-xs ${STATUS_CLASS[row.status]}`}
                >
                  {row.status}
                </span>
              </div>
              <p className="mt-2 text-sm text-ds-text-muted">{row.body}</p>
              {row.href ? (
                <div className="mt-3">
                  <Link
                    href={row.href}
                    className="text-sm text-ds-accent-lavender hover:underline"
                  >
                    Open →
                  </Link>
                </div>
              ) : null}
            </InnerPageSection>
          ))}
        </section>

        <InnerPageSection className="text-center">
          <p className="text-sm text-ds-text-muted">
            Privacy: {SITE_PRIVACY_EMAIL} · Legal: {SITE_LEGAL_EMAIL}
          </p>
          <div className="mt-4 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/security" variant="lavender">
              Security Center
            </ButtonLink>
            <ButtonLink href="/status" variant="ghost">
              System status
            </ButtonLink>
            <ButtonLink href="/privacy" variant="ghost">
              Privacy Policy
            </ButtonLink>
          </div>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
