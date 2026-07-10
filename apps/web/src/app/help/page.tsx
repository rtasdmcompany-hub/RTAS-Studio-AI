import type { Metadata } from "next";
import Link from "next/link";
import { PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";

export const metadata: Metadata = {
  title: `Help Center · ${PRODUCT_NAME}`,
  description: `Guides, support, and troubleshooting for ${PRODUCT_NAME}.`,
};

const TOPICS = [
  {
    href: "/how-to-use",
    title: "How to use",
    body: "Step-by-step studio walkthrough and category tips.",
  },
  {
    href: "/help/faq",
    title: "FAQ",
    body: "Credits, downloads, sign-in, and first-project answers.",
  },
  {
    href: "/help/billing",
    title: "Billing & credits",
    body: "Plans, renewals, commercial license, and downloads.",
  },
  {
    href: "/help/troubleshooting",
    title: "Troubleshooting",
    body: "Fix common issues without developer tools.",
  },
  {
    href: "/help/contact",
    title: "Contact support",
    body: "Email, feedback, and live chat FAQ.",
  },
  {
    href: "/help/changelog",
    title: "Changelog",
    body: "What’s new for creators.",
  },
  {
    href: "/feedback",
    title: "Feedback & requests",
    body: "Report a bug or suggest a feature.",
  },
  {
    href: "/profile",
    title: "Your dashboard",
    body: "Credits, queue, library, and account status.",
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
          <p className="rtas-eyebrow">Help Center</p>
          <h1 className="text-zinc-100">How can we help?</h1>
          <p className="mx-auto mt-3 max-w-2xl text-ds-text-muted">
            Everything you need to create with confidence — guides, billing clarity,
            and a direct line to support.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/studio" variant="lavender">
              Open Studio
            </ButtonLink>
            <ButtonLink href="/help/contact" variant="ghost">
              Contact support
            </ButtonLink>
          </div>
        </InnerPageSection>

        <section aria-labelledby="help-topics" className="grid gap-4 md:grid-cols-2">
          <h2 id="help-topics" className="sr-only">
            Help topics
          </h2>
          {TOPICS.map((t) => (
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
            <Link href="/help/faq" className="text-ds-accent-lavender underline-offset-2 hover:underline">
              See all FAQ →
            </Link>
          </p>
        </InnerPageSection>

        <InnerPageSection className="text-center">
          <h2 className="text-xl text-zinc-100">Still stuck?</h2>
          <p className="mt-2 text-sm text-ds-text-muted">
            Knowledge base articles and video tutorials expand as we launch
            internationally. Until then, email support or leave feedback.
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
