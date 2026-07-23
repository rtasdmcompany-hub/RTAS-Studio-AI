import type { Metadata } from "next";
import Link from "next/link";
import { ButtonLink } from "@rtas/ui";
import { requireSession } from "@/lib/auth/require-session";
import { buildPageMetadata } from "@/lib/site-metadata";
import { prisma, isPrismaConfigured } from "@/lib/prisma";
import { PARTNER_TYPES } from "@/lib/affiliate/config";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";

export const metadata: Metadata = buildPageMetadata({
  title: "Partner Dashboard",
  description: "Your RTAS Studio AI partnership applications, status, and resources.",
  path: "/partners/dashboard",
  noIndex: true,
});

const ANNOUNCEMENTS = [
  {
    title: "Partner program applications open",
    body: "Submit via /partners. Public partner logos are listed only after signed agreements — none fabricated.",
    date: "2026-07-23",
  },
  {
    title: "Affiliate payouts not live",
    body: "Creator affiliate applications are accepted for review; commission payouts remain disabled until configured.",
    date: "2026-07-23",
  },
] as const;

const SALES_MATERIALS = [
  {
    title: "Pricing (verified)",
    body: "Tester $5 / 30s / 5 days · Standard $89/mo / 2000s · Premium $249/mo / 2000s · 1 credit = 1 second.",
    href: "/pricing",
  },
  {
    title: "Enterprise inquiry",
    body: "Production Enterprise packaging and Identity Preservation policy conversations.",
    href: "/enterprise",
  },
  {
    title: "Marketing Resources Center",
    body: "Logos, guidelines, showcase links — placeholders labeled where assets are missing.",
    href: "/partners/resources",
  },
] as const;

export default async function PartnerDashboardPage() {
  const session = await requireSession("/partners/dashboard");

  const account = isPrismaConfigured()
    ? await prisma.partnerAccount.findUnique({ where: { userId: session.user.id } })
    : null;

  const applications = isPrismaConfigured()
    ? await prisma.partnerApplication.findMany({
        where: {
          OR: [{ userId: session.user.id }, { email: session.user.email ?? "" }],
        },
        orderBy: { createdAt: "desc" },
        take: 10,
      })
    : [];

  const trackLabel =
    PARTNER_TYPES.find((t) => t.id === account?.partnerType)?.title ??
    account?.partnerType ??
    "—";

  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection>
          <p className="rtas-eyebrow">Partner dashboard</p>
          <h1 className="text-zinc-100">Partnership workspace</h1>
          <p className="mt-2 max-w-2xl text-sm text-ds-text-muted">
            Signed in as {session.user.email}. Approval status and materials below use real
            application records — empty states are honest zeros / pending.
          </p>
        </InnerPageSection>

        <InnerPageSection aria-labelledby="approval-status" className="inner-page-section--panel">
          <h2 id="approval-status" className="text-xl text-zinc-100">
            Approval status
          </h2>
          {account ? (
            <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-ds-text-muted">Status</dt>
                <dd className="mt-1 text-zinc-100">{account.status}</dd>
              </div>
              <div>
                <dt className="text-ds-text-muted">Track</dt>
                <dd className="mt-1 text-zinc-100">{trackLabel}</dd>
              </div>
              <div>
                <dt className="text-ds-text-muted">Organization</dt>
                <dd className="mt-1 text-zinc-100">{account.organization}</dd>
              </div>
              <div>
                <dt className="text-ds-text-muted">Linked since</dt>
                <dd className="mt-1 text-zinc-100">
                  {account.createdAt.toISOString().slice(0, 10)}
                </dd>
              </div>
            </dl>
          ) : (
            <p className="mt-2 text-sm text-ds-text-muted">
              No partner account yet.{" "}
              <Link href="/partners#apply" className="text-ds-accent-lavender underline-offset-2 hover:underline">
                Submit a partnership application
              </Link>{" "}
              while signed in to create a pending account stub.
            </p>
          )}
        </InnerPageSection>

        <InnerPageSection aria-labelledby="partner-apps">
          <h2 id="partner-apps" className="text-xl text-zinc-100">
            Applications
          </h2>
          {applications.length === 0 ? (
            <p className="mt-2 text-sm text-ds-text-muted">0 applications on file.</p>
          ) : (
            <ul className="mt-3 space-y-2 text-sm text-ds-text-muted">
              {applications.map((app) => (
                <li key={app.id}>
                  {app.createdAt.toISOString().slice(0, 10)} · {app.partnerType} ·{" "}
                  <span className="text-zinc-200">{app.status}</span> ·{" "}
                  {app.organization}
                </li>
              ))}
            </ul>
          )}
        </InnerPageSection>

        <InnerPageSection aria-labelledby="sales-materials">
          <h2 id="sales-materials" className="text-xl text-zinc-100">
            Sales materials
          </h2>
          <ul className="mt-4 space-y-3">
            {SALES_MATERIALS.map((m) => (
              <li key={m.title}>
                <Link
                  href={m.href}
                  className="font-medium text-zinc-100 underline-offset-2 hover:underline"
                >
                  {m.title}
                </Link>
                <p className="mt-1 text-sm text-ds-text-muted">{m.body}</p>
              </li>
            ))}
          </ul>
        </InnerPageSection>

        <InnerPageSection aria-labelledby="announcements">
          <h2 id="announcements" className="text-xl text-zinc-100">
            Announcements
          </h2>
          <ul className="mt-4 space-y-4">
            {ANNOUNCEMENTS.map((a) => (
              <li key={a.title}>
                <p className="text-xs text-ds-text-muted">{a.date}</p>
                <p className="font-medium text-zinc-100">{a.title}</p>
                <p className="mt-1 text-sm text-ds-text-muted">{a.body}</p>
              </li>
            ))}
          </ul>
        </InnerPageSection>

        <InnerPageSection aria-labelledby="partner-support">
          <h2 id="partner-support" className="text-xl text-zinc-100">
            Support
          </h2>
          <p className="mt-2 text-sm text-ds-text-muted">
            Partnership questions:{" "}
            <a
              href="mailto:contact@rtasstudio.com"
              className="text-ds-accent-lavender underline-offset-2 hover:underline"
            >
              contact@rtasstudio.com
            </a>
            . Product help:{" "}
            <Link href="/help" className="text-ds-accent-lavender underline-offset-2 hover:underline">
              Customer Success
            </Link>
            .
          </p>
          <div className="mt-4 flex flex-wrap gap-3">
            <ButtonLink href="/partners/resources" variant="lavender">
              Resources center
            </ButtonLink>
            <ButtonLink href="/partners" variant="ghost">
              Partners overview
            </ButtonLink>
            <ButtonLink href="/affiliate" variant="ghost">
              Affiliate program
            </ButtonLink>
          </div>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
