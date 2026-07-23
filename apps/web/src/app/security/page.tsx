import type { Metadata } from "next";
import Link from "next/link";
import { PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";
import { StructuredData } from "@/components/seo/StructuredData";
import { buildPageMetadata } from "@/lib/site-metadata";
import { breadcrumbSchema } from "@/lib/structured-data";
import {
  SITE_HELP_EMAIL,
  SITE_LEGAL_EMAIL,
  SITE_SUPPORT_EMAIL,
} from "@/lib/site-links";

export const metadata: Metadata = buildPageMetadata({
  title: "Security Center",
  description: `Account security practices for ${PRODUCT_NAME} — password, sessions, tips, and how we report suspicious activity. Not a certification claim.`,
  path: "/security",
  openGraphTitle: `Security Center · ${PRODUCT_NAME}`,
  openGraphDescription:
    "Account security, session posture, and operational practices — Implemented vs Roadmap only.",
});

const ACCOUNT_ITEMS = [
  {
    title: "Password & sign-in",
    body: "Email/password accounts can reset credentials via Forgot password. Google OAuth accounts authenticate with Google — we never store Google passwords.",
    href: "/auth/forgot-password",
    label: "Reset password",
    status: "Implemented",
  },
  {
    title: "Email verification",
    body: "Sensitive API routes require a verified email when verification is enabled for the account.",
    href: "/auth/signin",
    label: "Sign in",
    status: "Implemented",
  },
  {
    title: "Active sessions",
    body: "Auth uses JWT sessions (up to 30 days). Privacy settings show the current browser session. Multi-device session list and remote revoke are Roadmap.",
    href: "/profile/privacy",
    label: "Privacy settings",
    status: "Partial",
  },
  {
    title: "Two-factor authentication (2FA)",
    body: "TOTP / passkey 2FA is not shipped. Marked Roadmap — do not claim MFA is available today.",
    href: "/profile/privacy",
    label: "Account privacy",
    status: "Roadmap",
  },
] as const;

const TIPS = [
  "Use a unique password and enable a password manager.",
  "Never share Credits, API keys, or admin secrets in chat or screenshots.",
  "Only upload likenesses you are authorized to use (Identity Preservation).",
  "Sign out on shared devices after Studio sessions.",
  "Treat unexpected “verify your account” emails carefully — check the From domain.",
] as const;

const PLATFORM = [
  {
    title: "Encryption in transit",
    body: "TLS for web and API traffic. Secrets stay server-side.",
    status: "Implemented",
  },
  {
    title: "Payment webhook integrity",
    body: "Merchant-of-Record webhooks fail closed on invalid signatures.",
    status: "Implemented",
  },
  {
    title: "Rate limiting",
    body: "Sensitive forms and APIs apply rate limits to reduce abuse.",
    status: "Implemented",
  },
  {
    title: "SOC 2 / ISO 27001 certification",
    body: "Not obtained. We maintain a compliance-ready posture and documentation — not a certification badge.",
    status: "Roadmap",
  },
] as const;

export default function SecurityCenterPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <StructuredData
          data={breadcrumbSchema([
            { name: "Home", path: "/" },
            { name: "Security Center", path: "/security" },
          ])}
        />
        <InnerPageSection className="text-center">
          <p className="rtas-eyebrow">Trust</p>
          <h1 className="text-white">Security Center</h1>
          <p className="mx-auto mt-3 max-w-2xl text-ds-text-muted">
            How {PRODUCT_NAME} protects accounts and what you can do today. Status labels are
            honest: Implemented, Partial, or Roadmap — never fabricated audit certifications.
          </p>
        </InnerPageSection>

        <section className="grid gap-4 md:grid-cols-2" aria-labelledby="sec-account">
          <h2 id="sec-account" className="sr-only">
            Account security
          </h2>
          {ACCOUNT_ITEMS.map((item) => (
            <InnerPageSection key={item.title}>
              <div className="flex flex-wrap items-start justify-between gap-2">
                <h3 className="text-lg text-white">{item.title}</h3>
                <span className="text-xs text-ds-text-muted">{item.status}</span>
              </div>
              <p className="mt-2 text-sm text-ds-text-muted">{item.body}</p>
              <div className="mt-4">
                <ButtonLink href={item.href} variant="ghost">
                  {item.label}
                </ButtonLink>
              </div>
            </InnerPageSection>
          ))}
        </section>

        <InnerPageSection aria-labelledby="sec-tips">
          <h2 id="sec-tips" className="text-xl text-white">
            Security tips
          </h2>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-ds-text-muted">
            {TIPS.map((tip) => (
              <li key={tip}>{tip}</li>
            ))}
          </ul>
        </InnerPageSection>

        <section className="grid gap-4 md:grid-cols-2" aria-labelledby="sec-platform">
          <h2 id="sec-platform" className="sr-only">
            Platform practices
          </h2>
          {PLATFORM.map((item) => (
            <InnerPageSection key={item.title}>
              <div className="flex flex-wrap items-start justify-between gap-2">
                <h3 className="text-lg text-white">{item.title}</h3>
                <span className="text-xs text-ds-text-muted">{item.status}</span>
              </div>
              <p className="mt-2 text-sm text-ds-text-muted">{item.body}</p>
            </InnerPageSection>
          ))}
        </section>

        <InnerPageSection aria-labelledby="sec-suspicious">
          <h2 id="sec-suspicious" className="text-xl text-white">
            Suspicious activity
          </h2>
          <p className="mt-3 text-sm text-ds-text-muted">
            If you see unrecognized logins, unexpected Credit usage, or phishing that
            impersonates {PRODUCT_NAME}, sign out, reset your password if you use
            credentials, and email {SITE_HELP_EMAIL} with the account email, approximate
            time, and any job IDs. Copyright issues: {SITE_LEGAL_EMAIL}. General:{" "}
            {SITE_SUPPORT_EMAIL}.
          </p>
          <div className="mt-4 flex flex-wrap gap-3">
            <ButtonLink href="/profile/privacy" variant="lavender">
              Privacy &amp; sessions
            </ButtonLink>
            <ButtonLink href="/compliance" variant="ghost">
              Compliance Center
            </ButtonLink>
            <ButtonLink href="/help/contact" variant="ghost">
              Contact support
            </ButtonLink>
            <Link href="/trust-safety" className="text-sm text-ds-accent-lavender self-center">
              Trust &amp; Safety →
            </Link>
          </div>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
