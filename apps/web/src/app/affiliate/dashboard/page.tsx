import type { Metadata } from "next";
import Link from "next/link";
import { ButtonLink } from "@rtas/ui";
import { requireSession } from "@/lib/auth/require-session";
import { buildPageMetadata } from "@/lib/site-metadata";
import { prisma, isPrismaConfigured } from "@/lib/prisma";
import {
  AFFILIATE_COOKIE_DAYS,
  AFFILIATE_PAYOUTS_LIVE,
  buildReferralUrl,
  generateReferralCode,
} from "@/lib/affiliate/config";
import { getNextAuthUrl } from "@/lib/env";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";

export const metadata: Metadata = buildPageMetadata({
  title: "Affiliate Dashboard",
  description: "Your RTAS Studio AI affiliate referral link, metrics, and payment status.",
  path: "/affiliate/dashboard",
  noIndex: true,
});

async function ensureAffiliateAccount(userId: string) {
  if (!isPrismaConfigured()) return null;
  const existing = await prisma.affiliateAccount.findUnique({ where: { userId } });
  if (existing) return existing;
  let code = generateReferralCode(userId);
  const clash = await prisma.affiliateAccount.findUnique({ where: { referralCode: code } });
  if (clash) code = generateReferralCode(`${userId}-${Date.now()}`);
  return prisma.affiliateAccount.create({
    data: {
      userId,
      referralCode: code,
      status: "pending",
      paymentStatus: "not_connected",
    },
  });
}

export default async function AffiliateDashboardPage() {
  const session = await requireSession("/affiliate/dashboard");
  const account = await ensureAffiliateAccount(session.user.id);
  const applications = isPrismaConfigured()
    ? await prisma.affiliateApplication.findMany({
        where: {
          OR: [{ userId: session.user.id }, { email: session.user.email ?? "" }],
        },
        orderBy: { createdAt: "desc" },
        take: 5,
      })
    : [];

  const origin = getNextAuthUrl().replace(/\/$/, "");
  const referralCode = account?.referralCode ?? "—";
  const referralLink =
    account?.referralCode != null ? buildReferralUrl(account.referralCode, origin) : "Not connected";

  const clicks = account?.clicks ?? 0;
  const signups = account?.signups ?? 0;
  const paid = account?.paidConversions ?? 0;
  const commissionCents = account?.commissionCents ?? 0;
  const paymentStatus = account?.paymentStatus ?? "not_connected";
  const status = account?.status ?? "pending";

  const metrics = [
    { label: "Clicks", value: String(clicks), note: clicks === 0 ? "Tracking not connected" : "" },
    { label: "Signups", value: String(signups), note: signups === 0 ? "No attributed signups" : "" },
    { label: "Paid conversions", value: String(paid), note: paid === 0 ? "No paid conversions" : "" },
    {
      label: "Commission",
      value: `$${(commissionCents / 100).toFixed(2)}`,
      note: AFFILIATE_PAYOUTS_LIVE ? "" : "Payouts not live — balance is informational only",
    },
  ];

  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection>
          <p className="rtas-eyebrow">Affiliate dashboard</p>
          <h1 className="text-zinc-100">Your referrals</h1>
          <p className="mt-2 max-w-2xl text-sm text-ds-text-muted">
            Signed in as {session.user.email}. Metrics show real zeros until attribution tooling is
            connected. Account status: <span className="text-zinc-200">{status}</span>.
          </p>
          {!AFFILIATE_PAYOUTS_LIVE ? (
            <p className="mt-4 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-sm text-amber-100/90">
              Commission payouts are <strong>not live</strong>. Do not treat dashboard figures as
              payable earnings.
            </p>
          ) : null}
        </InnerPageSection>

        <InnerPageSection aria-labelledby="referral-link">
          <h2 id="referral-link" className="text-xl text-zinc-100">
            Referral link & code
          </h2>
          <dl className="mt-4 space-y-3 text-sm">
            <div>
              <dt className="text-ds-text-muted">Referral code</dt>
              <dd className="mt-1 font-mono text-zinc-100">{referralCode}</dd>
            </div>
            <div>
              <dt className="text-ds-text-muted">Referral link</dt>
              <dd className="mt-1 break-all font-mono text-zinc-100">{referralLink}</dd>
            </div>
            <div>
              <dt className="text-ds-text-muted">Cookie window</dt>
              <dd className="mt-1 text-zinc-100">{AFFILIATE_COOKIE_DAYS} days</dd>
            </div>
          </dl>
        </InnerPageSection>

        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4" aria-labelledby="affiliate-metrics">
          <InnerPageSection className="sm:col-span-2 lg:col-span-4 pb-2">
            <h2 id="affiliate-metrics" className="text-xl text-zinc-100">
              Performance
            </h2>
          </InnerPageSection>
          {metrics.map((m) => (
            <InnerPageSection key={m.label} className="inner-page-section--panel">
              <p className="text-sm text-ds-text-muted">{m.label}</p>
              <p className="mt-2 text-2xl text-zinc-100">{m.value}</p>
              {m.note ? <p className="mt-1 text-xs text-amber-200/80">{m.note}</p> : null}
            </InnerPageSection>
          ))}
        </section>

        <InnerPageSection aria-labelledby="payment-status">
          <h2 id="payment-status" className="text-xl text-zinc-100">
            Payment status
          </h2>
          <p className="mt-2 text-sm text-ds-text-muted">
            Status:{" "}
            <span className="text-zinc-100">
              {paymentStatus === "not_connected" ? "Not connected" : paymentStatus}
            </span>
            . Payout rails are not connected until ops enables affiliate payouts.
          </p>
        </InnerPageSection>

        <InnerPageSection aria-labelledby="commission-history">
          <h2 id="commission-history" className="text-xl text-zinc-100">
            Commission history
          </h2>
          <p className="mt-2 text-sm text-ds-text-muted">
            No commission events yet (0). History will appear here after attribution and payouts are
            connected — not fabricated.
          </p>
        </InnerPageSection>

        <InnerPageSection aria-labelledby="applications">
          <h2 id="applications" className="text-xl text-zinc-100">
            Your applications
          </h2>
          {applications.length === 0 ? (
            <p className="mt-2 text-sm text-ds-text-muted">
              No applications on file.{" "}
              <Link href="/affiliate#apply" className="text-ds-accent-lavender underline-offset-2 hover:underline">
                Apply now
              </Link>
              .
            </p>
          ) : (
            <ul className="mt-3 space-y-2 text-sm text-ds-text-muted">
              {applications.map((app) => (
                <li key={app.id}>
                  {app.createdAt.toISOString().slice(0, 10)} · status{" "}
                  <span className="text-zinc-200">{app.status}</span> · id{" "}
                  <span className="font-mono text-zinc-300">{app.id.slice(0, 8)}…</span>
                </li>
              ))}
            </ul>
          )}
        </InnerPageSection>

        <InnerPageSection aria-labelledby="assets">
          <h2 id="assets" className="text-xl text-zinc-100">
            Marketing assets
          </h2>
          <p className="mt-2 text-sm text-ds-text-muted">
            Use the Marketing Resources Center for logos and guidelines. Missing creatives are
            labeled placeholders.
          </p>
          <div className="mt-4 flex flex-wrap gap-3">
            <ButtonLink href="/partners/resources" variant="lavender">
              Open resources
            </ButtonLink>
            <ButtonLink href="/affiliate" variant="ghost">
              Program overview
            </ButtonLink>
            <ButtonLink href="/profile" variant="ghost">
              Account dashboard
            </ButtonLink>
          </div>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
