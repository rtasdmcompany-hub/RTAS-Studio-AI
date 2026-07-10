import type { Metadata } from "next";
import Link from "next/link";
import { PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";

export const metadata: Metadata = {
  title: `Changelog · Help · ${PRODUCT_NAME}`,
  description: `Product updates for ${PRODUCT_NAME}.`,
};

const HIGHLIGHTS = [
  {
    label: "Productization",
    body: "Dashboard welcome flow, Help Center, Feedback, clearer empty states, and full SaaS documentation pack.",
  },
  {
    label: "Enterprise hardening",
    body: "Rate limits, fail-closed webhooks, email-verified API sessions, share URL allowlist, and upload validation.",
  },
  {
    label: "Studio & Dashboard",
    body: "First-time guidance, credits visibility, generation progress, and library empty-state CTAs.",
  },
] as const;

export default function HelpChangelogPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection>
          <p className="rtas-eyebrow">
            <Link href="/help" className="text-ds-accent-lavender">
              Help Center
            </Link>{" "}
            · Changelog
          </p>
          <h1 className="text-zinc-100">What&apos;s new</h1>
          <p className="mt-3 max-w-2xl text-ds-text-muted">
            Highlights for creators. Full engineering notes live in the repository
            release docs.
          </p>
        </InnerPageSection>

        <div className="grid gap-4">
          {HIGHLIGHTS.map((h) => (
            <InnerPageSection key={h.label}>
              <h2 className="text-lg text-zinc-100">{h.label}</h2>
              <p className="mt-2 text-sm text-ds-text-muted">{h.body}</p>
            </InnerPageSection>
          ))}
        </div>

        <InnerPageSection className="text-center">
          <ButtonLink href="/studio" variant="lavender">
            Open Studio
          </ButtonLink>
          <ButtonLink href="/feedback" variant="ghost" className="ml-3">
            Request a feature
          </ButtonLink>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
