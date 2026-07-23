import type { Metadata } from "next";
import Link from "next/link";
import { PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";
import { AffiliateApplicationForm } from "@/components/affiliate/AffiliateApplicationForm";
import { buildPageMetadata } from "@/lib/site-metadata";
import {
  AFFILIATE_COOKIE_DAYS,
  AFFILIATE_COMMISSION_PLACEHOLDER,
  AFFILIATE_MIN_PAYOUT_USD,
  AFFILIATE_PAYOUT_NET_DAYS,
  AFFILIATE_PAYOUTS_LIVE,
  AFFILIATE_PROGRAM_STATUS,
} from "@/lib/affiliate/config";

export const metadata: Metadata = buildPageMetadata({
  title: "Affiliate Program",
  description: `Apply to the ${PRODUCT_NAME} affiliate program. Applications open for review — commission payouts are not live until configured. Placeholder rates only.`,
  path: "/affiliate",
  openGraphTitle: `Affiliate Program · ${PRODUCT_NAME}`,
  openGraphDescription:
    "Refer creators and agencies to RTAS Studio AI. Applications accepted for review; payouts are not live until attribution and payment rails are configured.",
});

const BENEFITS = [
  {
    title: "ICP-fit product",
    body: "Promote cinematic AI video with Authorized Identity Preservation — Tester $5, Standard $89/mo, Premium $249/mo — without inventing free credits.",
  },
  {
    title: "Clear attribution window",
    body: `Cookie / referral attribution window: ${AFFILIATE_COOKIE_DAYS} days (configurable via AFFILIATE_COOKIE_DAYS).`,
  },
  {
    title: "Honest program posture",
    body: "We will not publish fake partner counts or live earnings claims. Rates stay labeled as placeholders until confirmed in writing.",
  },
  {
    title: "Marketing kit access",
    body: "Approved affiliates get the Marketing Resources Center — logos, guidelines, and templates (placeholders where assets are still missing).",
  },
] as const;

const FAQ = [
  {
    q: "Are affiliate payouts live today?",
    a: AFFILIATE_PAYOUTS_LIVE
      ? "Payout rails are flagged as enabled in this environment — confirm ops readiness before promoting earnings."
      : "No. Applications are open for review only. Do not market this as a live earnings program until RTAS enables payouts.",
  },
  {
    q: "What are the commission rates?",
    a: `${AFFILIATE_COMMISSION_PLACEHOLDER.label}: illustrative ${AFFILIATE_COMMISSION_PLACEHOLDER.standardFirstMonthPercent} of first Standard month and ${AFFILIATE_COMMISSION_PLACEHOLDER.premiumFirstMonthPercent} of first Premium month. Final rates are confirmed in writing before any payment.`,
  },
  {
    q: "How long is the cookie window?",
    a: `${AFFILIATE_COOKIE_DAYS} days from the referral click (env/constant). Tracking is stubbed until attribution tooling is connected.`,
  },
  {
    q: "When would payouts happen?",
    a: `Placeholder schedule: monthly, Net-${AFFILIATE_PAYOUT_NET_DAYS}, once a minimum of $${AFFILIATE_MIN_PAYOUT_USD} is reached — only after payouts are enabled.`,
  },
  {
    q: "What promotions are forbidden?",
    a: "Unauthorized likeness / deepfake claims, fake “unlimited free” offers, trademark bidding without approval, and incentivized fake signups.",
  },
] as const;

export default function AffiliatePage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="text-center">
          <p className="rtas-eyebrow">Affiliate program</p>
          <h1 className="text-zinc-100">Refer RTAS Studio AI</h1>
          <p className="mx-auto mt-3 max-w-2xl text-ds-text-muted">
            Applications are open for review. Status:{" "}
            <span className="text-zinc-200">
              {AFFILIATE_PROGRAM_STATUS === "applications_open_payouts_not_live"
                ? "applications open · payouts not live"
                : "payouts flagged enabled (verify ops)"}
            </span>
            . Commission figures below are placeholders — not a live offer.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <ButtonLink href="#apply" variant="lavender">
              Apply now
            </ButtonLink>
            <ButtonLink href="/affiliate/dashboard" variant="ghost">
              Affiliate dashboard
            </ButtonLink>
            <ButtonLink href="/partners/resources" variant="ghost">
              Marketing resources
            </ButtonLink>
          </div>
        </InnerPageSection>

        {!AFFILIATE_PAYOUTS_LIVE ? (
          <InnerPageSection className="border border-amber-500/25 bg-amber-500/10 text-center">
            <h2 className="text-lg text-amber-50">Payouts not live</h2>
            <p className="mx-auto mt-2 max-w-2xl text-sm text-amber-100/85">
              RTAS is accepting applications and building attribution. Do not advertise guaranteed
              commissions or live earnings until payouts are explicitly enabled and confirmed in
              your agreement.
            </p>
          </InnerPageSection>
        ) : null}

        <section className="grid gap-4 md:grid-cols-2" aria-labelledby="affiliate-benefits">
          <InnerPageSection className="md:col-span-2 text-center pb-2">
            <h2 id="affiliate-benefits" className="text-xl text-zinc-100">
              Benefits
            </h2>
          </InnerPageSection>
          {BENEFITS.map((b) => (
            <InnerPageSection key={b.title}>
              <h3 className="text-lg text-zinc-100">{b.title}</h3>
              <p className="mt-2 text-sm text-ds-text-muted">{b.body}</p>
            </InnerPageSection>
          ))}
        </section>

        <InnerPageSection aria-labelledby="commission-structure">
          <h2 id="commission-structure" className="text-xl text-zinc-100">
            Commission structure (placeholder)
          </h2>
          <p className="mt-2 text-sm font-medium text-amber-200/90">
            {AFFILIATE_COMMISSION_PLACEHOLDER.label}
          </p>
          <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-ds-text-muted">
            <li>
              Standard first month: {AFFILIATE_COMMISSION_PLACEHOLDER.standardFirstMonthPercent} of
              $89 (illustrative)
            </li>
            <li>
              Premium first month: {AFFILIATE_COMMISSION_PLACEHOLDER.premiumFirstMonthPercent} of
              $249 (illustrative)
            </li>
            <li>Base: {AFFILIATE_COMMISSION_PLACEHOLDER.base}</li>
            <li>{AFFILIATE_COMMISSION_PLACEHOLDER.testerNote}</li>
            <li>
              Cookie duration: {AFFILIATE_COOKIE_DAYS} days · Payout schedule: monthly Net-
              {AFFILIATE_PAYOUT_NET_DAYS} · Min payout: ${AFFILIATE_MIN_PAYOUT_USD} (when live)
            </li>
          </ul>
          <p className="mt-4 text-sm text-ds-text-muted">
            Full detail:{" "}
            <Link
              href="/partners"
              className="text-ds-accent-lavender underline-offset-2 hover:underline"
            >
              Partners hub
            </Link>
            . Program docs live in the repository under{" "}
            <code className="text-zinc-300">docs/partners/</code>.
          </p>
        </InnerPageSection>

        <InnerPageSection aria-labelledby="affiliate-terms">
          <h2 id="affiliate-terms" className="text-xl text-zinc-100">
            Program terms (summary)
          </h2>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-ds-text-muted">
            <li>
              Disclose the affiliate relationship per FTC / applicable advertising rules.
            </li>
            <li>
              Use approved product claims only — no face-swap / deepfake positioning; Identity
              Preservation is authorized-content only.
            </li>
            <li>
              Price truthfully: Tester $5 / 30s / 5 days; Standard $89/mo / 2000s; Premium $249/mo /
              2000s; 1 credit = 1 second; no free credit plan.
            </li>
            <li>
              Site{" "}
              <Link href="/terms" className="text-ds-accent-lavender underline-offset-2 hover:underline">
                Terms of Service
              </Link>
              ,{" "}
              <Link href="/privacy" className="text-ds-accent-lavender underline-offset-2 hover:underline">
                Privacy Policy
              </Link>
              , and{" "}
              <Link href="/ai-policy" className="text-ds-accent-lavender underline-offset-2 hover:underline">
                AI Usage Policy
              </Link>{" "}
              apply. A signed affiliate agreement governs payouts when enabled.
            </li>
          </ul>
        </InnerPageSection>

        <InnerPageSection aria-labelledby="affiliate-faq">
          <h2 id="affiliate-faq" className="text-xl text-zinc-100">
            FAQ
          </h2>
          <dl className="mt-4 space-y-4">
            {FAQ.map((item) => (
              <div key={item.q}>
                <dt className="font-medium text-zinc-100">{item.q}</dt>
                <dd className="mt-1 text-sm text-ds-text-muted">{item.a}</dd>
              </div>
            ))}
          </dl>
        </InnerPageSection>

        <InnerPageSection id="apply" aria-labelledby="affiliate-apply">
          <h2 id="affiliate-apply" className="text-xl text-zinc-100">
            Apply now
          </h2>
          <p className="mt-2 max-w-xl text-sm text-ds-text-muted">
            Sign in before applying if you want a referral code stub on your dashboard. Applications
            are stored securely and emailed to the RTAS team when mail delivery is configured.
          </p>
          <div className="mt-6 max-w-xl">
            <AffiliateApplicationForm />
          </div>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
