import type { Metadata } from "next";
import Link from "next/link";
import { PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";
import { PromotionPlacement } from "@/components/promotions/PromotionPlacement";
import { PRODUCT_VERSION } from "@/lib/release-notes";
import { buildPageMetadata } from "@/lib/site-metadata";
import { SITE_SOCIAL_LINKS } from "@/lib/site-links";

export const metadata: Metadata = buildPageMetadata({
  title: "Customer Success Center",
  description: `Customer Success Center for ${PRODUCT_NAME} — getting started, tutorials, knowledge base, FAQs, release notes, best practices, community, roadmap, and support.`,
  path: "/success",
  openGraphTitle: `Customer Success · ${PRODUCT_NAME}`,
});

const DISCORD =
  SITE_SOCIAL_LINKS.find((l) => l.id === "discord")?.href ?? "https://discord.gg/rtas";

const LINKS = [
  {
    href: "/how-to-use",
    title: "Getting Started",
    body: "Step-by-step studio walkthrough for your first authorized render.",
  },
  {
    href: "/showcase",
    title: "Tutorials & Showcase",
    body: "Watch product showcases and reference cinematic output.",
  },
  {
    href: "/help",
    title: "Knowledge Base",
    body: "Searchable Help Center across account, billing, credits, and generation.",
  },
  {
    href: "/help/faq",
    title: "FAQs",
    body: "Categorized answers for creators and teams.",
  },
  {
    href: "/help/changelog",
    title: "Release Notes",
    body: `Version ${PRODUCT_VERSION} — features, fixes, and known issues.`,
  },
  {
    href: "/help/troubleshooting",
    title: "Best Practices",
    body: "Troubleshooting and practical guidance to finish jobs successfully.",
  },
  {
    href: DISCORD,
    title: "Community",
    body: "Discord for product tips and peer discussion.",
    external: true,
  },
  {
    href: "/engage",
    title: "Engagement Center",
    body: "Tips, tutorials, announcements, and community (Sprint 3–4).",
  },
  {
    href: "/roadmap",
    title: "Product Roadmap",
    body: "Honest roadmap signals — no fake vote counts.",
  },
  {
    href: "/tickets",
    title: "Support Tickets",
    body: "Open a ticket with category, priority, and attachments metadata.",
  },
  {
    href: "/retention",
    title: "Retention Center",
    body: "Usage insights, upgrades, tips, learning, and milestones (sign-in).",
  },
  {
    href: "/profile/health",
    title: "Customer Health",
    body: "Your account health from real usage — never invented scores.",
  },
  {
    href: "/feedback",
    title: "CSAT / NPS & Feedback",
    body: "Bug, feature, suggestion, CSAT, and NPS — stored when submitted.",
  },
  {
    href: "/help/contact",
    title: "Contact Support",
    body: "Email and Discord when you need a human.",
  },
  {
    href: "/status",
    title: "System Status",
    body: "Live health probes for the production web app.",
  },
] as const;

export default function SuccessCenterPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="text-center">
          <p className="rtas-eyebrow">RTAS Studio AI</p>
          <h1 className="text-zinc-100">Customer Success Center</h1>
          <p className="mx-auto mt-3 max-w-2xl text-ds-text-muted">
            One place for onboarding, knowledge, community, and support — built for creators
            and teams using {PRODUCT_NAME}. Empty states stay empty until real activity exists.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/studio" variant="lavender">
              Open Studio
            </ButtonLink>
            <ButtonLink href="/help" variant="ghost">
              Search Help
            </ButtonLink>
            <ButtonLink href="/tickets" variant="ghost">
              Open a ticket
            </ButtonLink>
          </div>
        </InnerPageSection>

        <section
          aria-labelledby="success-hub"
          className="grid gap-4 md:grid-cols-2 lg:grid-cols-3"
        >
          <h2 id="success-hub" className="sr-only">
            Success hub links
          </h2>
          {LINKS.map((t) =>
            "external" in t && t.external ? (
              <a
                key={t.title}
                href={t.href}
                target="_blank"
                rel="noopener noreferrer"
                className="inner-page-section block transition hover:border-ds-accent-lavender/40"
              >
                <h3 className="text-lg text-zinc-100">{t.title}</h3>
                <p className="mt-2 text-sm text-ds-text-muted">{t.body}</p>
              </a>
            ) : (
              <Link
                key={t.title}
                href={t.href}
                className="inner-page-section block transition hover:border-ds-accent-lavender/40"
              >
                <h3 className="text-lg text-zinc-100">{t.title}</h3>
                <p className="mt-2 text-sm text-ds-text-muted">{t.body}</p>
              </Link>
            )
          )}
        </section>

        <PromotionPlacement
          placement="learning_center"
          pagePath="/success"
          title="Learning recommendations"
          emptyMinHeightClassName="min-h-[14rem]"
        />
      </InnerPageContainer>
    </MarketingLayout>
  );
}
