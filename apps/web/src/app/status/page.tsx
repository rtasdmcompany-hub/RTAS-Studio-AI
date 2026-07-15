import type { Metadata } from "next";
import { PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";

export const metadata: Metadata = {
  title: "System status",
  description: `Operational status for ${PRODUCT_NAME} — web app, generation API, auth, billing, and live health probes.`,
  openGraph: {
    title: `System status · ${PRODUCT_NAME}`,
    description:
      "Service cards, live /api/health and /api/ready links, and incident history for this deployment.",
  },
};

const SERVICES = [
  {
    name: "Web App",
    status: "Operational",
    body: "Marketing site, Studio UI, dashboard, and authenticated app routes served by this deployment.",
  },
  {
    name: "Generation API",
    status: "Operational",
    body: "Credit-guarded render pipeline and job polling used by Studio. Availability depends on configured GPU providers and readiness checks.",
  },
  {
    name: "Auth",
    status: "Operational",
    body: "NextAuth sessions, email verification, and optional Google OAuth for sign-in and account access.",
  },
  {
    name: "Billing",
    status: "Operational",
    body: "Merchant of Record checkout and webhooks (Paddle / Lemon Squeezy) that update subscription and credit state server-side.",
  },
] as const;

const PROBES = [
  {
    title: "Health",
    body: "Lightweight liveness probe used by hosting and uptime monitors. Confirms the web process is up.",
    href: "/api/health",
    label: "Open /api/health",
  },
  {
    title: "Readiness",
    body: "Dependency-aware readiness check for deploy and ops gates. Public response is minimal by design.",
    href: "/api/ready",
    label: "Open /api/ready",
  },
] as const;

export default function StatusPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="text-center">
          <p className="rtas-eyebrow">Status</p>
          <h1 className="text-white">System status</h1>
          <p className="mx-auto mt-3 max-w-2xl text-ds-text-muted">
            Current operational view for {PRODUCT_NAME}. Service cards reflect the intended
            production posture for this deployment; open the live probes below for JSON from
            the running instance.
          </p>
          <p className="mt-4 inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-4 py-1.5 text-sm text-emerald-300">
            <span
              className="inline-block h-2 w-2 rounded-full bg-emerald-400"
              aria-hidden
            />
            All systems operational
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
                <span className="inline-flex items-center gap-1.5 text-xs font-medium text-emerald-300">
                  <span
                    className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-400"
                    aria-hidden
                  />
                  {service.status}
                </span>
              </div>
              <p className="mt-2 text-sm text-ds-text-muted">{service.body}</p>
            </InnerPageSection>
          ))}
        </section>

        <section className="grid gap-4 md:grid-cols-2" aria-label="Live probes">
          {PROBES.map((item) => (
            <InnerPageSection key={item.title} className="text-center">
              <h2 className="text-lg text-white">{item.title}</h2>
              <p className="mt-2 text-sm text-ds-text-muted">{item.body}</p>
              <div className="mt-4">
                <ButtonLink href={item.href} variant="lavender">
                  {item.label}
                </ButtonLink>
              </div>
            </InnerPageSection>
          ))}
        </section>

        <InnerPageSection aria-labelledby="status-incidents">
          <h2 id="status-incidents" className="text-xl text-white">
            Incident history
          </h2>
          <p className="mt-3 text-sm text-ds-text-muted">
            No open incidents. When an incident is active, we post a short summary here with
            affected services and next updates. For account-specific issues that are not a
            platform outage, use Help Center.
          </p>
          <ul className="mt-4 space-y-2 text-sm text-ds-text-muted">
            <li className="flex flex-wrap gap-x-3 gap-y-1">
              <span className="text-zinc-100">Past 90 days</span>
              <span>No recorded platform incidents on this status surface.</span>
            </li>
          </ul>
        </InnerPageSection>

        <InnerPageSection className="text-center">
          <p className="text-sm text-ds-text-muted">
            Account or billing issues? Visit Help Center — status pages are for service
            health only.
          </p>
          <div className="mt-4 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/help" variant="ghost">
              Help Center
            </ButtonLink>
            <ButtonLink href="/developers" variant="ghost">
              Developers
            </ButtonLink>
            <ButtonLink href="/help/contact" variant="ghost">
              Contact
            </ButtonLink>
          </div>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
