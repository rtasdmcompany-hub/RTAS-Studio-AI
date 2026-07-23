import type { Metadata } from "next";
import { PRODUCT_NAME, TESTER_PRICE_USD } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";
import { MarketingSubscribeForm } from "@/components/marketing/MarketingSubscribeForm";
import { buildPageMetadata } from "@/lib/site-metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Updates & tips",
  description: `Subscribe to ${PRODUCT_NAME} product updates, early access notes, and AI video tips. Not a free credit plan.`,
  path: "/updates",
});

export default function UpdatesPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="text-center">
          <p className="rtas-eyebrow">Stay informed</p>
          <h1 className="text-zinc-100">Product updates & AI tips</h1>
          <p className="mx-auto mt-3 max-w-2xl text-ds-text-muted">
            Minimal email lists for creators evaluating {PRODUCT_NAME}. Subscribing does not
            grant generation credits — Tester (${TESTER_PRICE_USD}) or a subscription is required
            to render.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/studio" variant="lavender">
              Start creating
            </ButtonLink>
            <ButtonLink href="/pricing" variant="ghost">
              View pricing
            </ButtonLink>
          </div>
        </InnerPageSection>

        <InnerPageSection className="mx-auto max-w-lg">
          <MarketingSubscribeForm
            kind="product_updates"
            source="updates_page"
            allowKindSelect
            title="Choose a list"
            description="Newsletter, product updates, AI tips, or early access — one email field, privacy consent required."
          />
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
