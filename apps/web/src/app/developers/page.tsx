import type { Metadata } from "next";
import { PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";

export const metadata: Metadata = {
  title: "Developers",
  description: `Developer resources for ${PRODUCT_NAME} — public health and share APIs, auth notes, rate limits, and status.`,
  openGraph: {
    title: `Developers · ${PRODUCT_NAME}`,
    description:
      "Documented BFF patterns: health, readiness, share, webhooks — plus auth and rate-limit guidance.",
  },
};

const PUBLIC_ENDPOINTS = [
  {
    method: "GET",
    path: "/api/health",
    auth: "None",
    body: "Liveness JSON for the web service (`status`, `service`, `timestamp`). Use for uptime monitors and load balancers. Does not validate databases or GPU workers.",
  },
  {
    method: "GET",
    path: "/api/ready",
    auth: "None (minimal)",
    body: "Readiness probe for deploy and ops gates. Public response stays minimal; detailed dependency checks require an authorized admin request.",
  },
  {
    method: "GET",
    path: "/api/share/[videoId]",
    auth: "None",
    body: "Returns the public share payload for a published video. Responds 404 when the video is not shared. Pair with the public `/share/[videoId]` page for client review.",
  },
] as const;

const AUTHENTICATED_PATTERNS = [
  {
    method: "POST",
    path: "/api/share/[videoId]",
    auth: "Session required",
    body: "Publishes a generation job for public viewing. Validates the video URL against allowed app and media hosts. Rate limited per authenticated user and client IP.",
  },
  {
    method: "POST",
    path: "/api/webhooks/paddle",
    auth: "Provider signature",
    body: "Paddle Merchant of Record webhooks update subscription state server-side. Configure the published URL in your Paddle dashboard; treat as fail-closed on invalid signatures.",
  },
  {
    method: "POST",
    path: "/api/webhooks/lemon-squeezy",
    auth: "Provider signature",
    body: "Lemon Squeezy webhooks for subscription and order events when that MoR is active. Same fail-closed verification model as Paddle.",
  },
] as const;

const TOPICS = [
  {
    title: "Health & readiness",
    body: "Monitor liveness via /api/health and readiness via /api/ready. Open live JSON from the Status page for this deployment.",
    href: "/status",
  },
  {
    title: "Payments webhooks",
    body: "Paddle and Lemon Squeezy webhooks update subscription state server-side. Point your merchant dashboard at the published webhook routes.",
    href: "/help/billing",
  },
  {
    title: "Share links",
    body: "Generated videos can be published through the share API and public /share/[videoId] pages for social and client review.",
    href: "/showcase",
  },
  {
    title: "Source & issues",
    body: "The product monorepo and release notes live on GitHub. Prefer Help Center for account issues; use GitHub for engineering discussion.",
    href: "https://github.com/rtasdmcompany-hub/RTAS-Studio-AI",
  },
] as const;

export default function DevelopersPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="text-center">
          <p className="rtas-eyebrow">Developers</p>
          <h1 className="text-white">Build with {PRODUCT_NAME}</h1>
          <p className="mx-auto mt-3 max-w-2xl text-ds-text-muted">
            Integration notes for operators and engineers — health probes, billing webhooks,
            and share surfaces. This documents the existing web BFF; it is not a general
            public generation SDK. Creator workflow docs stay under Documentation and How to
            use.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/status" variant="lavender">
              System status
            </ButtonLink>
            <ButtonLink href="/docs" variant="ghost">
              Product docs
            </ButtonLink>
          </div>
        </InnerPageSection>

        <section aria-labelledby="dev-public-api">
          <InnerPageSection className="pb-2">
            <h2 id="dev-public-api" className="text-xl text-white">
              Public API endpoints
            </h2>
            <p className="mt-2 max-w-2xl text-sm text-ds-text-muted">
              Safe to call without a user session. Prefer these for monitoring and reading
              published shares.
            </p>
          </InnerPageSection>
          <div className="grid gap-4">
            {PUBLIC_ENDPOINTS.map((item) => (
              <InnerPageSection key={`${item.method}-${item.path}`}>
                <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                  <code className="text-xs font-semibold text-ds-accent-lavender">
                    {item.method}
                  </code>
                  <code className="text-sm text-zinc-100">{item.path}</code>
                  <span className="text-xs text-ds-text-muted">{item.auth}</span>
                </div>
                <p className="mt-2 text-sm text-ds-text-muted">{item.body}</p>
              </InnerPageSection>
            ))}
          </div>
        </section>

        <section aria-labelledby="dev-auth-patterns">
          <InnerPageSection className="pb-2">
            <h2 id="dev-auth-patterns" className="text-xl text-white">
              Authenticated & webhook patterns
            </h2>
            <p className="mt-2 max-w-2xl text-sm text-ds-text-muted">
              Documented for operators integrating checkout and share. Generation, upload,
              checkout, and account routes under <code className="text-zinc-100">/api/*</code>{" "}
              require a valid NextAuth session (or webhook signature) and are intended for
              the first-party web app — not for inventing third-party private API clients.
            </p>
          </InnerPageSection>
          <div className="grid gap-4">
            {AUTHENTICATED_PATTERNS.map((item) => (
              <InnerPageSection key={`${item.method}-${item.path}`}>
                <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                  <code className="text-xs font-semibold text-ds-accent-lavender">
                    {item.method}
                  </code>
                  <code className="text-sm text-zinc-100">{item.path}</code>
                  <span className="text-xs text-ds-text-muted">{item.auth}</span>
                </div>
                <p className="mt-2 text-sm text-ds-text-muted">{item.body}</p>
              </InnerPageSection>
            ))}
          </div>
        </section>

        <section className="grid gap-4 md:grid-cols-2" aria-labelledby="dev-auth-limits">
          <h2 id="dev-auth-limits" className="sr-only">
            Auth and rate limits
          </h2>
          <InnerPageSection>
            <h3 className="text-lg text-white">Authentication notes</h3>
            <ul className="mt-3 space-y-2 text-sm text-ds-text-muted">
              <li>
                Browser sessions use NextAuth (email credentials and optional Google OAuth).
              </li>
              <li>
                Authenticated BFF routes call session helpers server-side; unauthenticated
                callers receive standard HTTP error responses.
              </li>
              <li>
                Webhooks authenticate via provider signatures — never expose merchant secrets
                to the client.
              </li>
              <li>
                Admin-detailed readiness checks require an authorized admin secret header.
              </li>
            </ul>
          </InnerPageSection>
          <InnerPageSection>
            <h3 className="text-lg text-white">Rate limits (conceptual)</h3>
            <ul className="mt-3 space-y-2 text-sm text-ds-text-muted">
              <li>
                Sensitive mutations (for example share publish) apply per-user and per-IP
                windows and return retry-after style responses when exceeded.
              </li>
              <li>
                Generation and checkout paths are credit- and session-guarded; treat them as
                first-party app traffic, not open bulk APIs.
              </li>
              <li>
                Health and readiness are safe for frequent polling; keep intervals reasonable
                for your monitor (typically tens of seconds or more).
              </li>
              <li>
                Abusive traffic may be blocked at the edge or application layer without prior
                notice.
              </li>
            </ul>
          </InnerPageSection>
        </section>

        <section className="grid gap-4 md:grid-cols-2" aria-label="Developer topics">
          {TOPICS.map((item) => (
            <InnerPageSection key={item.title}>
              <h2 className="text-lg text-white">{item.title}</h2>
              <p className="mt-2 text-sm text-ds-text-muted">{item.body}</p>
              <div className="mt-4">
                {item.href.startsWith("http") ? (
                  <a
                    href={item.href}
                    className="rtas-btn-ghost rtas-ui-btn"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Open →
                  </a>
                ) : (
                  <ButtonLink href={item.href} variant="ghost">
                    Open →
                  </ButtonLink>
                )}
              </div>
            </InnerPageSection>
          ))}
        </section>

        <InnerPageSection className="text-center">
          <h2 className="text-xl text-white">Support vs engineering</h2>
          <p className="mx-auto mt-2 max-w-xl text-sm text-ds-text-muted">
            Account, credits, and download questions go to Help Center. Platform status and
            API surfaces are documented here for technical teams.
          </p>
          <div className="mt-5 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/docs" variant="lavender">
              Documentation
            </ButtonLink>
            <ButtonLink href="/status" variant="ghost">
              Status
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
