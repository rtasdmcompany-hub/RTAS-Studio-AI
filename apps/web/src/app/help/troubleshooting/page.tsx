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
  title: `Troubleshooting · Help · ${PRODUCT_NAME}`,
  description: `Fix common issues in ${PRODUCT_NAME} without developer tools.`,
};

const STEPS = [
  {
    title: "Can’t sign in",
    body: "Confirm your email first (check spam). Use “Forgot?” only if you set a password. Google sign-in requires the same email you registered with.",
  },
  {
    title: "Studio won’t generate",
    body: "Check credits on your Dashboard. If the queue is full, wait for a slot. Refresh once — drafts autosave, so you won’t lose work.",
  },
  {
    title: "No email arrived",
    body: "Wait a minute, check spam/promotions, then use Resend on the check-email screen. Still stuck? Email support with your account address.",
  },
  {
    title: "Video stuck processing",
    body: "Longer videos take longer. Watch Dashboard notifications and your inbox. If status hasn’t changed after the estimated window, contact support with the project time.",
  },
  {
    title: "Download blocked",
    body: "Previews can’t be downloaded. Subscribe or ensure your plan is active, then open the finished video from Your library.",
  },
] as const;

export default function HelpTroubleshootingPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection>
          <p className="rtas-eyebrow">
            <Link href="/help" className="text-ds-accent-lavender">
              Help Center
            </Link>{" "}
            · Troubleshooting
          </p>
          <h1 className="text-zinc-100">Fix it fast</h1>
          <p className="mt-3 max-w-2xl text-ds-text-muted">
            Customer-safe steps — no environment variables or developer setup required.
          </p>
        </InnerPageSection>

        <div className="grid gap-4">
          {STEPS.map((s) => (
            <InnerPageSection key={s.title}>
              <h2 className="text-lg text-zinc-100">{s.title}</h2>
              <p className="mt-2 text-sm text-ds-text-muted">{s.body}</p>
            </InnerPageSection>
          ))}
        </div>

        <InnerPageSection className="text-center">
          <ButtonLink href="/feedback" variant="primary">
            Report a bug
          </ButtonLink>
          <ButtonLink href="/help/contact" variant="ghost" className="ml-3">
            Contact support
          </ButtonLink>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
