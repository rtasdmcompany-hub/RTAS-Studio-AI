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
  title: `FAQ · Help · ${PRODUCT_NAME}`,
  description: `Frequently asked questions about ${PRODUCT_NAME}.`,
};

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
    q: "How long does a render take?",
    a: "Most short clips finish in a few minutes. Longer videos are built in segments and stitched automatically — you’ll get an email when ready.",
  },
  {
    q: "Can I use videos commercially?",
    a: "Yes, when you have an active paid subscription. Commercial license entitlement is included with Standard and Premium plans.",
  },
  {
    q: "How do I contact support?",
    a: "Email support@rtasdigital.com or use Feedback in the app. Include your account email and a short description of the issue.",
  },
] as const;

export default function HelpFaqPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection>
          <p className="rtas-eyebrow">
            <Link href="/help" className="text-ds-accent-lavender">
              Help Center
            </Link>{" "}
            · FAQ
          </p>
          <h1 className="text-zinc-100">Common questions</h1>
          <p className="mt-3 max-w-2xl text-ds-text-muted">
            Clear answers for first-time creators and returning teams.
          </p>
        </InnerPageSection>

        <InnerPageSection>
          <dl className="space-y-6 text-left">
            {FAQ.map((item) => (
              <div key={item.q}>
                <dt className="font-medium text-zinc-100">{item.q}</dt>
                <dd className="mt-2 text-sm text-ds-text-muted">{item.a}</dd>
              </div>
            ))}
          </dl>
        </InnerPageSection>

        <InnerPageSection className="text-center">
          <ButtonLink href="/help/contact" variant="primary">
            Contact support
          </ButtonLink>
          <ButtonLink href="/how-to-use" variant="ghost" className="ml-3">
            Product guide
          </ButtonLink>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
