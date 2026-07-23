import type { Metadata } from "next";
import { PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";
import { buildPageMetadata } from "@/lib/site-metadata";
import { LiveStatusProbes } from "@/components/status/LiveStatusProbes";
import { CookieSettingsButton } from "@/components/marketing/CookieSettingsButton";

export const metadata: Metadata = buildPageMetadata({
  title: "System status",
  description: `Operational status for ${PRODUCT_NAME} — web app, generation API, auth, billing, and live health probes.`,
  path: "/status",
  openGraphTitle: `System status · ${PRODUCT_NAME}`,
  openGraphDescription:
    "Live health for web, GPU worker, auth, billing webhooks, and third-party integrations.",
});

const SERVICES = [
  {
    name: "Web App",
    probe: "live" as const,
    body: "Marketing site, Studio UI, dashboard, and authenticated app routes served by this deployment.",
  },
  {
    name: "Generation API / GPU",
    probe: "live" as const,
    body: "Credit-guarded render pipeline and GPU workers. Live readiness reflects FastAPI/config probes; capacity may still vary under load.",
  },
  {
    name: "Database",
    probe: "live" as const,
    body: "Primary application database (configured via DATABASE_URL). Public probes confirm configuration readiness without exposing connection details.",
  },
  {
    name: "Persistent storage",
    probe: "live" as const,
    body: "KV/Redis or equivalent store used for sessions/cache where configured (required on Vercel production).",
  },
  {
    name: "Email delivery",
    probe: "live" as const,
    body: "Transactional mail (verification, resets, notifications) via Resend or SMTP when configured.",
  },
  {
    name: "Auth",
    probe: "live" as const,
    body: "NextAuth sessions, email verification, and optional Google OAuth for sign-in and account access.",
  },
  {
    name: "Billing",
    probe: "live" as const,
    body: "Merchant of Record checkout and webhooks (Paddle / Lemon Squeezy) that update subscription and credit state server-side.",
  },
] as const;

const MAINTENANCE = {
  active: false,
  summary:
    "No scheduled maintenance window is published on this page right now. When maintenance is planned, we post start/end windows here and in Help Center announcements.",
};

const INCIDENTS: Array<{
  id: string;
  date: string;
  title: string;
  status: "resolved" | "monitoring" | "investigating";
  summary: string;
}> = [
  // Real incidents only — do not invent outages. Structure ready for ops entries.
];

export default function StatusPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="text-center">
          <p className="rtas-eyebrow">Status</p>
          <h1 className="text-white">System status</h1>
          <p className="mx-auto mt-3 max-w-2xl text-ds-text-muted">
            Operational view for {PRODUCT_NAME}. Service cards describe each subsystem;
            live probes below report HTTP health from this deployment. Placeholder labels
            are used only when a dependency cannot be probed publicly without leaking secrets.
          </p>
          <p className="mt-4 inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-4 py-1.5 text-sm text-emerald-300">
            <span
              className="inline-block h-2 w-2 rounded-full bg-emerald-400"
              aria-hidden
            />
            Check live probes for current health
          </p>
        </InnerPageSection>

        <section
          className="grid gap-4 md:grid-cols-2"
          aria-labelledby="status-services"
        >
          <h2 id="status-services" className="sr-only">
            Services
          </h2>
          {SERVICES.map((service) => (
            <InnerPageSection key={service.name}>
              <div className="flex flex-wrap items-start justify-between gap-2">
                <h3 className="text-lg text-white">{service.name}</h3>
                <span className="inline-flex items-center gap-1.5 text-xs font-medium text-sky-200">
                  <span
                    className="inline-block h-1.5 w-1.5 rounded-full bg-sky-400"
                    aria-hidden
                  />
                  Probe-backed
                </span>
              </div>
              <p className="mt-2 text-sm text-ds-text-muted">{service.body}</p>
            </InnerPageSection>
          ))}
        </section>

        <InnerPageSection aria-labelledby="status-maint">
          <h2 id="status-maint" className="text-xl text-white">
            Maintenance
          </h2>
          <p className="mt-3 text-sm text-ds-text-muted">
            {MAINTENANCE.active
              ? "Maintenance is active — see announcement channels for details."
              : MAINTENANCE.summary}
          </p>
        </InnerPageSection>

        <InnerPageSection aria-labelledby="status-incidents">
          <h2 id="status-incidents" className="text-xl text-white">
            Incident history
          </h2>
          <p className="mt-3 text-sm text-ds-text-muted">
            Structured history for platform incidents. Entries are added only when a real
            incident is recorded by ops — this list is not fabricated for marketing.
          </p>
          {INCIDENTS.length === 0 ? (
            <ul className="mt-4 space-y-2 text-sm text-ds-text-muted">
              <li className="flex flex-wrap gap-x-3 gap-y-1">
                <span className="text-zinc-100">Past 90 days</span>
                <span>No recorded platform incidents on this status surface.</span>
              </li>
            </ul>
          ) : (
            <ul className="mt-4 space-y-3">
              {INCIDENTS.map((inc) => (
                <li
                  key={inc.id}
                  className="rounded-lg border border-ds-border-subtle bg-ds-surface-glass p-4 text-sm"
                >
                  <div className="flex flex-wrap justify-between gap-2">
                    <span className="font-medium text-zinc-100">{inc.title}</span>
                    <span className="text-ds-text-muted">
                      {inc.date} · {inc.status}
                    </span>
                  </div>
                  <p className="mt-2 text-ds-text-muted">{inc.summary}</p>
                </li>
              ))}
            </ul>
          )}
        </InnerPageSection>

        <InnerPageSection>
          <LiveStatusProbes />
        </InnerPageSection>

        <InnerPageSection className="text-center">
          <div className="mt-4 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/help" variant="ghost">
              Help Center
            </ButtonLink>
            <ButtonLink href="/security" variant="ghost">
              Security
            </ButtonLink>
            <ButtonLink href="/compliance" variant="ghost">
              Compliance
            </ButtonLink>
            <ButtonLink href="/help/contact" variant="ghost">
              Contact
            </ButtonLink>
            <CookieSettingsButton />
          </div>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
