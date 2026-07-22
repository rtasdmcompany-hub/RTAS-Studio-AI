import type { Metadata } from "next";
import Link from "next/link";
import { PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";
import { PRODUCT_VERSION } from "@/lib/release-notes";
import { buildPageMetadata } from "@/lib/site-metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Customer Success Center",
  description: `Customer Success Center for ${PRODUCT_NAME} — Knowledge Base, FAQ, Support, Guides, Video Tutorials, and Release Notes.`,
  path: "/help",
  openGraphTitle: `Customer Success · ${PRODUCT_NAME}`,
});

const HUB = [
  {
    href: "/help/faq",
    title: "Knowledge Base / FAQ",
    body: "Credits, downloads, sign-in, and first-project answers.",
  },
  {
    href: "/help/troubleshooting",
    title: "Troubleshooting",
    body: "Fix common Studio and account issues without developer tools.",
  },
  {
    href: "/help/billing",
    title: "Billing & credits",
    body: "Plans, renewals, commercial license, and downloads.",
  },
  {
    href: "/help/contact",
    title: "Support & Contact",
    body: "Email, Discord community, and product feedback channels.",
  },
  {
    href: "/how-to-use",
    title: "Guides",
    body: "Step-by-step studio walkthrough and category tips.",
  },
  {
    href: "/showcase",
    title: "Video Tutorials / Showcase",
    body: "Watch product showcases and reference cinematic output.",
  },
  {
    href: "/help/changelog",
    title: "Release Notes",
    body: `Version ${PRODUCT_VERSION} — features, improvements, fixes, and known issues.`,
  },
  {
    href: "/feedback",
    title: "Feedback & requests",
    body: "Report a bug or suggest a feature.",
  },
  {
    href: "/beta",
    title: "Public Beta",
    body: "Eligibility, limitations, and apply for early access.",
  },
  {
    href: "/enterprise",
    title: "Enterprise sales",
    body: "Demo, proposal, or meeting for brands and teams.",
  },
  {
    href: "/partners",
    title: "Partnerships",
    body: "Technology, agencies, affiliate, and education tracks.",
  },
  {
    href: "/status",
    title: "System status",
    body: "Live health probes and operational posture.",
  },
] as const;

const FAQ_PREVIEW = [
  {
    q: "Where do I start after signing up?",
    a: "Open your Dashboard, then launch Studio. A short welcome guide appears on first visit.",
  },
  {
    q: "What is a credit?",
    a: "1 credit equals 1 second of finished video.",
  },
  {
    q: "Why can’t I download a preview?",
    a: "Free previews are for review only. Paid plans unlock downloadable masters.",
  },
] as const;

export default function HelpPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="text-center">
          <p className="rtas-eyebrow">Customer Success Center</p>
          <h1 className="text-zinc-100">How can we help?</h1>
          <p className="mx-auto mt-3 max-w-2xl text-ds-text-muted">
            Knowledge Base, support, guides, release notes, and commercial paths — one hub for
            creators and teams using {PRODUCT_NAME}.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/studio" variant="lavender">
              Open Studio
            </ButtonLink>
            <ButtonLink href="/help/contact" variant="ghost">
              Contact support
            </ButtonLink>
            <ButtonLink href="/help/changelog" variant="ghost">
              Release notes
            </ButtonLink>
          </div>
        </InnerPageSection>

        <section aria-labelledby="csc-hub" className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <h2 id="csc-hub" className="sr-only">
            Customer Success hub
          </h2>
          {HUB.map((t) => (
            <Link
              key={t.href}
              href={t.href}
              className="inner-page-section block transition hover:border-ds-accent-lavender/40"
            >
              <h3 className="text-lg text-zinc-100">{t.title}</h3>
              <p className="mt-2 text-sm text-ds-text-muted">{t.body}</p>
            </Link>
          ))}
        </section>

        <InnerPageSection aria-labelledby="help-faq">
          <h2 id="help-faq" className="text-xl text-zinc-100">
            Quick answers
          </h2>
          <dl className="mt-6 space-y-6 text-left">
            {FAQ_PREVIEW.map((item) => (
              <div key={item.q}>
                <dt className="font-medium text-zinc-100">{item.q}</dt>
                <dd className="mt-2 text-sm text-ds-text-muted">{item.a}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-6 text-sm">
            <Link
              href="/help/faq"
              className="text-ds-accent-lavender underline-offset-2 hover:underline"
            >
              See all FAQ →
            </Link>
          </p>
        </InnerPageSection>

        <InnerPageSection className="text-center">
          <h2 className="text-xl text-zinc-100">Still stuck?</h2>
          <p className="mt-2 text-sm text-ds-text-muted">
            Knowledge base articles expand as we launch internationally. Until then, email
            support or leave feedback — we do not invent ticket SLAs we cannot keep.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/feedback" variant="primary">
              Send feedback
            </ButtonLink>
            <ButtonLink href="/how-to-use" variant="ghost">
              Full product guide
            </ButtonLink>
          </div>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
