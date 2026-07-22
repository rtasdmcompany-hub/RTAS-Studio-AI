import type { Metadata } from "next";
import Link from "next/link";
import { PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";
import { CommercialLeadForm } from "@/components/commercial/CommercialLeadForm";
import { buildPageMetadata } from "@/lib/site-metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Public Beta",
  description: `Apply for the ${PRODUCT_NAME} public beta — eligibility, features, limitations, privacy, and terms. Honest early access for creators evaluating Identity Preservation video.`,
  path: "/beta",
  openGraphTitle: `Public Beta · ${PRODUCT_NAME}`,
  openGraphDescription:
    "Early access for creators and teams evaluating RTAS Studio AI. Apply with validated form — no fake waitlists or invented capacity claims.",
});

const FEATURES = [
  {
    title: "Full Studio workflow",
    body: "Compose → Render → Publish with credits metering (1 credit = 1 second) and live job progress.",
  },
  {
    title: "Identity Preservation (authorized)",
    body: "Authorized likeness workflows only — you must have rights to any identity you lock. Unauthorized use is prohibited.",
  },
  {
    title: "Transparent plans",
    body: "Tester $5 · Standard $89/mo · Premium $249/mo. Beta does not invent free unlimited usage.",
  },
  {
    title: "Help & feedback loops",
    body: "Help Center, changelog, and feedback channels so early users can shape the product honestly.",
  },
] as const;

const LIMITATIONS = [
  "Live paid checkout depends on Merchant-of-Record (Paddle) enablement on the seller account.",
  "Cloud GPU generation requires provider wallet balance — renders may queue or fail if the pool is empty.",
  "Enterprise SSO, custom SLAs, and dedicated VPC deployment are not part of public beta.",
  "We do not claim fake beta seats, waitlist size, or customer logos.",
] as const;

const FEEDBACK_EXPECTATIONS = [
  "Report blockers and confusing steps via /feedback (Bug / Feature / General) within a few days of first use.",
  "Share one real project outcome when you can — what worked, what failed, what you expected.",
  "Do not invent reviews or testimonials for marketing; we only publish feedback you explicitly approve.",
] as const;

const SUPPORT_CHANNELS = [
  {
    title: "Email",
    body: "contact@rtasstudio.com — account, billing, and beta access questions.",
    href: "mailto:contact@rtasstudio.com",
    cta: "Email support",
    external: true,
  },
  {
    title: "Product feedback",
    body: "Bug reports, feature requests, ratings — validated form with email delivery when configured.",
    href: "/feedback",
    cta: "Open feedback",
    external: false,
  },
  {
    title: "Help Center",
    body: "FAQ, troubleshooting, billing, and changelog for self-serve answers.",
    href: "/help",
    cta: "Browse help",
    external: false,
  },
] as const;

const ELIGIBILITY = [
  "Creators, freelancers, agencies, and brands evaluating AI video for real projects.",
  "Willingness to provide constructive feedback via /feedback or support email.",
  "Acceptance of Terms of Service and Privacy Policy at application time.",
  "Authorized rights for any Identity Preservation / likeness materials you upload.",
] as const;

export default function PublicBetaPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="text-center">
          <p className="rtas-eyebrow">Public Beta</p>
          <h1 className="text-zinc-100">Early access to {PRODUCT_NAME}</h1>
          <p className="mx-auto mt-3 max-w-2xl text-ds-text-muted">
            Join the public beta to evaluate Studio, credits, and Identity Preservation on real
            work. Capacity is limited by infrastructure — applications are reviewed; we do not
            invent waitlist numbers or fake acceptance rates.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <ButtonLink href="#apply" variant="lavender">
              Apply for Beta
            </ButtonLink>
            <ButtonLink href="/pricing" variant="ghost">
              View pricing
            </ButtonLink>
          </div>
        </InnerPageSection>

        <section className="grid gap-4 md:grid-cols-2" aria-labelledby="beta-eligibility">
          <InnerPageSection className="md:col-span-2 text-center pb-2">
            <h2 id="beta-eligibility" className="text-xl text-zinc-100">
              Eligibility
            </h2>
          </InnerPageSection>
          {ELIGIBILITY.map((item) => (
            <InnerPageSection key={item}>
              <p className="text-sm text-ds-text-muted">{item}</p>
            </InnerPageSection>
          ))}
        </section>

        <section className="grid gap-4 md:grid-cols-2" aria-labelledby="beta-features">
          <InnerPageSection className="md:col-span-2 text-center pb-2">
            <h2 id="beta-features" className="text-xl text-zinc-100">
              What you get
            </h2>
          </InnerPageSection>
          {FEATURES.map((f) => (
            <InnerPageSection key={f.title}>
              <h3 className="text-lg text-zinc-100">{f.title}</h3>
              <p className="mt-2 text-sm text-ds-text-muted">{f.body}</p>
            </InnerPageSection>
          ))}
        </section>

        <InnerPageSection aria-labelledby="beta-limitations">
          <h2 id="beta-limitations" className="text-xl text-zinc-100">
            Limitations (honest)
          </h2>
          <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-ds-text-muted">
            {LIMITATIONS.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <p className="mt-4 text-sm text-ds-text-muted">
            Full engineering notes:{" "}
            <Link href="/help/changelog" className="text-ds-accent-lavender hover:underline">
              Release notes
            </Link>
            .
          </p>
        </InnerPageSection>

        <InnerPageSection aria-labelledby="beta-feedback">
          <h2 id="beta-feedback" className="text-xl text-zinc-100">
            Feedback expectations
          </h2>
          <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-ds-text-muted">
            {FEEDBACK_EXPECTATIONS.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </InnerPageSection>

        <section className="grid gap-4 md:grid-cols-3" aria-labelledby="beta-support">
          <InnerPageSection className="md:col-span-3 text-center pb-2">
            <h2 id="beta-support" className="text-xl text-zinc-100">
              Support channels
            </h2>
          </InnerPageSection>
          {SUPPORT_CHANNELS.map((channel) => (
            <InnerPageSection key={channel.title}>
              <h3 className="text-lg text-zinc-100">{channel.title}</h3>
              <p className="mt-2 text-sm text-ds-text-muted">{channel.body}</p>
              <div className="mt-4">
                {channel.external ? (
                  <a href={channel.href} className="rtas-btn-ghost rtas-ui-btn">
                    {channel.cta} →
                  </a>
                ) : (
                  <ButtonLink href={channel.href} variant="ghost">
                    {channel.cta} →
                  </ButtonLink>
                )}
              </div>
            </InnerPageSection>
          ))}
        </section>

        <InnerPageSection aria-labelledby="beta-privacy">
          <h2 id="beta-privacy" className="text-xl text-zinc-100">
            Privacy & terms
          </h2>
          <p className="mt-3 max-w-2xl text-sm text-ds-text-muted">
            Application data (name, email, use case) is used only to evaluate beta access and
            reply to you. See our{" "}
            <Link href="/privacy" className="text-ds-accent-lavender hover:underline">
              Privacy Policy
            </Link>{" "}
            and{" "}
            <Link href="/terms" className="text-ds-accent-lavender hover:underline">
              Terms of Service
            </Link>
            . Identity Preservation requires authorization for likeness content — see{" "}
            <Link href="/ai-policy" className="text-ds-accent-lavender hover:underline">
              AI Usage Policy
            </Link>
            .
          </p>
        </InnerPageSection>

        <InnerPageSection id="apply" aria-labelledby="beta-apply">
          <h2 id="beta-apply" className="text-xl text-zinc-100">
            Apply for Beta
          </h2>
          <p className="mt-2 max-w-xl text-sm text-ds-text-muted">
            Submit the form below. We notify the RTAS team by email when delivery is configured;
            otherwise you will see an honest error and can write to contact@rtasstudio.com.
          </p>
          <div className="mt-6 max-w-xl">
            <CommercialLeadForm
              kind="beta"
              submitLabel="Submit beta application"
              showRole
              showUseCase
              requireTerms
              messageLabel="Anything else we should know"
              messagePlaceholder="Timeline, markets, or specific Studio features you need…"
            />
          </div>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
