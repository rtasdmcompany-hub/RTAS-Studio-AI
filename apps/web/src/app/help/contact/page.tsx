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
  title: `Contact · Help · ${PRODUCT_NAME}`,
  description: `Contact support for ${PRODUCT_NAME}.`,
};

export default function HelpContactPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="text-center">
          <p className="rtas-eyebrow">
            <Link href="/help" className="text-ds-accent-lavender">
              Help Center
            </Link>{" "}
            · Contact
          </p>
          <h1 className="text-zinc-100">We&apos;re here to help</h1>
          <p className="mx-auto mt-3 max-w-xl text-ds-text-muted">
            Include your account email, what you were trying to do, and roughly when it
            happened. That helps us resolve issues faster.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <ButtonLink href="mailto:support@rtasdigital.com" variant="lavender">
              Email support@rtasdigital.com
            </ButtonLink>
            <ButtonLink href="/feedback" variant="primary">
              Send feedback
            </ButtonLink>
          </div>
        </InnerPageSection>

        <InnerPageSection>
          <h2 className="text-xl text-zinc-100">Other channels</h2>
          <ul className="mt-4 space-y-3 text-sm text-ds-text-muted">
            <li>
              <strong className="text-zinc-100">Live chat FAQ</strong> — available on
              marketing pages and in Studio for quick answers.
            </li>
            <li>
              <strong className="text-zinc-100">Knowledge base & tutorials</strong> —
              expanding for international launch (placeholders on Feedback).
            </li>
            <li>
              <strong className="text-zinc-100">Community</strong> — coming when CS
              capacity is ready.
            </li>
          </ul>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
