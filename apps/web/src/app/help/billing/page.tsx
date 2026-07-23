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

import { buildPageMetadata } from "@/lib/site-metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Billing & credits",
  description: `Billing & credits help for ${PRODUCT_NAME}: Tester $5, Standard $89/mo, Premium $249/mo, renewals, downloads, and Merchant of Record (Paddle) checkout.`,
  path: "/help/billing",
  openGraphTitle: `Billing & credits · Help · ${PRODUCT_NAME}`,
});

export default function HelpBillingPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection>
          <p className="rtas-eyebrow">
            <Link href="/help" className="text-ds-accent-lavender">
              Help Center
            </Link>{" "}
            · Billing
          </p>
          <h1 className="text-zinc-100">Plans, credits & downloads</h1>
          <p className="mt-3 max-w-2xl text-ds-text-muted">
            Payments are handled by our Merchant of Record, Paddle.
            Card data never touches RTAS servers.
          </p>
        </InnerPageSection>

        <InnerPageSection>
          <h2 className="text-xl text-zinc-100">Credits</h2>
          <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-ds-text-muted">
            <li>1 credit = 1 second of finished video.</li>
            <li>Monthly pools expire at the end of the billing period.</li>
            <li>Early resubscribe can roll over remaining credits when offered in-app.</li>
          </ul>
        </InnerPageSection>

        <InnerPageSection>
          <h2 className="text-xl text-zinc-100">Downloads & license</h2>
          <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-ds-text-muted">
            <li>Free / trial previews are for evaluation — watermarked, no commercial download.</li>
            <li>Active paid plans unlock downloadable masters and commercial entitlement.</li>
            <li>Manage your plan from Dashboard → Manage plans.</li>
          </ul>
        </InnerPageSection>

        <PromotionPlacement
          placement="billing_upgrade"
          pagePath="/help/billing"
          title="Recommended upgrades"
          emptyMinHeightClassName="min-h-[14rem]"
        />

        <InnerPageSection className="text-center">
          <ButtonLink href="/pricing" variant="lavender">
            View pricing
          </ButtonLink>
          <ButtonLink href="/profile" variant="ghost" className="ml-3">
            Open Dashboard
          </ButtonLink>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
