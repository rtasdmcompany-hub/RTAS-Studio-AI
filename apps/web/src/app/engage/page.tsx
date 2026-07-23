import type { Metadata } from "next";
import Link from "next/link";
import { PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";
import { buildPageMetadata } from "@/lib/site-metadata";
import { NewsletterSignup } from "@/components/marketing/NewsletterSignup";

export const metadata: Metadata = buildPageMetadata({
  title: "Engagement Center",
  description: `Tips, tutorials, getting started, knowledge base, announcements, and community for ${PRODUCT_NAME}.`,
  path: "/engage",
  openGraphTitle: `Engage · ${PRODUCT_NAME}`,
});

const SECTIONS = [
  {
    title: "Getting started",
    body: "Verify email, open Dashboard, launch Studio, set duration, generate. 1 credit = 1 second.",
    href: "/how-to-use",
    cta: "How to use",
  },
  {
    title: "Tips & tutorials",
    body: "Category tips, showcase references, and walkthroughs for commercials, music videos, and stories.",
    href: "/showcase",
    cta: "Watch showcase",
  },
  {
    title: "Knowledge Base",
    body: "FAQ, billing, troubleshooting, and release notes in Customer Success.",
    href: "/help",
    cta: "Open help",
  },
  {
    title: "Feature highlights",
    body: "Authorized Identity Preservation, second-based credits, Tester → Standard → Premium 4K path.",
    href: "/features",
    cta: "View features",
  },
  {
    title: "Announcements",
    body: "Product and maintenance notices appear in the header Notification Center when you are signed in.",
    href: "/profile/notifications",
    cta: "Notification preferences",
  },
  {
    title: "Community",
    body: "Discord for product tips and showcase feedback. Use email for account-sensitive billing.",
    href: "https://discord.gg/rtas",
    cta: "Join Discord",
    external: true,
  },
  {
    title: "Retention Center",
    body: "Usage insights, milestones, upgrades, and rule-based recovery tips (sign-in).",
    href: "/retention",
    cta: "Open retention",
  },
  {
    title: "Customer Success Center",
    body: "Full hub for onboarding, KB, tickets, health, and feedback.",
    href: "/success",
    cta: "Open success",
  },
  {
    title: "Refer a creator",
    body: "Invite colleagues with your referral link. Rewards are Proposed until the credit grant engine is live.",
    href: "/referral",
    cta: "Referral program",
  },
] as const;

export default function EngagePage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="pt-8">
          <p className="text-sm tracking-wide text-ds-text-muted">Customer Engagement</p>
          <h1 className="mt-2 font-display text-4xl text-ds-text md:text-5xl">
            {PRODUCT_NAME}
          </h1>
          <p className="mt-4 max-w-2xl text-ds-text-muted">
            One place for tips, tutorials, getting started, knowledge base links,
            announcements, features, and community — built for creators who ship.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <ButtonLink href="/studio" variant="primary">
              Open Studio
            </ButtonLink>
            <ButtonLink href="/help" variant="secondary">
              Customer Success
            </ButtonLink>
          </div>
        </InnerPageSection>

        <div className="grid gap-4 md:grid-cols-2">
          {SECTIONS.map((s) => (
            <InnerPageSection
              key={s.title}
              className="inner-page-section--panel"
            >
              <h2 className="text-xl text-ds-text">{s.title}</h2>
              <p className="mt-2 text-sm text-ds-text-muted">{s.body}</p>
              {s.external ? (
                <a
                  href={s.href}
                  className="mt-4 inline-block text-sm text-ds-accent underline-offset-4 hover:underline"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {s.cta} →
                </a>
              ) : (
                <Link
                  href={s.href}
                  className="mt-4 inline-block text-sm text-ds-accent underline-offset-4 hover:underline"
                >
                  {s.cta} →
                </Link>
              )}
            </InnerPageSection>
          ))}
        </div>

        <InnerPageSection className="inner-page-section--panel">
          <h2 className="text-xl text-ds-text">Newsletter</h2>
          <p className="mt-2 text-sm text-ds-text-muted">
            Opt in for product updates. Marketing emails respect unsubscribe /
            preferences. We do not invent subscriber counts.
          </p>
          <div className="mt-4">
            <NewsletterSignup />
          </div>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
