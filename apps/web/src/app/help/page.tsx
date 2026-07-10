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
    href: "/pricing",
    title: "Plans & credits",
    body: "Compare Tester, Standard, and Premium — and how credits work.",
  },
  {
    href: "/profile",
    title: "Your dashboard",
    body: "Credits, queue, library, and account status in one place.",
  },
  {
    href: "/feedback",
    title: "Feedback & requests",
    body: "Report a bug or suggest a feature for the product team.",
  },
] as const;

const FAQ = [
  {
    q: "Where do I start after signing up?",
    a: "Open your Dashboard to see credits, then launch Studio to create your first video. A short welcome guide appears on first visit.",
  },
  {
    q: "What is a credit?",
    a: "1 credit equals 1 second of finished video. Your plan grants a monthly credit pool that expires at the end of the billing period.",
  },
  {
    q: "Why can’t I download a preview?",
    a: "Free previews are for review only. Subscribe or use paid credits for downloadable masters and commercial license entitlement.",
  },
  {
    q: "How do I contact support?",
    a: "Email support@rtasdigital.com or use the live chat on marketing pages. Include your account email and a short description of the issue.",
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
            <ButtonLink href="mailto:support@rtasdigital.com" variant="ghost">
              Email support
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
            Common questions
          </h2>
          <dl className="mt-6 space-y-6 text-left">
            {FAQ.map((item) => (
              <div key={item.q}>
                <dt className="font-medium text-zinc-100">{item.q}</dt>
                <dd className="mt-2 text-sm text-ds-text-muted">{item.a}</dd>
              </div>
            ))}
          </dl>
        </InnerPageSection>

        <InnerPageSection className="text-center">
          <h2 className="text-xl text-zinc-100">Still stuck?</h2>
          <p className="mt-2 text-sm text-ds-text-muted">
            Knowledge base and video tutorials expand as we launch internationally.
            Until then, email support or leave feedback.
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
