import type { Metadata } from "next";
import Link from "next/link";
import { PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";
import { SITE_SUPPORT_EMAIL, SITE_SOCIAL_LINKS } from "@/lib/site-links";

export const metadata: Metadata = {
  title: `Contact · Help · ${PRODUCT_NAME}`,
  description: `Contact ${PRODUCT_NAME} support — email, Discord community, Help FAQ, and product feedback.`,
};

const DISCORD =
  SITE_SOCIAL_LINKS.find((l) => l.id === "discord")?.href ?? "https://discord.gg/rtas";

const CHANNELS = [
  {
    title: "Email support",
    body: `Write to ${SITE_SUPPORT_EMAIL} with your account email, what you were trying to do, and roughly when it happened. Include plan or invoice references for billing questions.`,
    href: `mailto:${SITE_SUPPORT_EMAIL}`,
    cta: `Email ${SITE_SUPPORT_EMAIL}`,
    external: true,
  },
  {
    title: "Discord community",
    body: "Join creators and the RTAS team for product tips, showcase feedback, and community discussion. For account-sensitive billing issues, prefer email so we can verify your account safely.",
    href: DISCORD,
    cta: "Open Discord",
    external: true,
  },
  {
    title: "Help FAQ",
    body: "Self-serve answers for credits, downloads, sign-in, first projects, and common Studio questions — often faster than waiting for a reply.",
    href: "/help/faq",
    cta: "Browse FAQ",
    external: false,
  },
  {
    title: "Product feedback",
    body: "Report a bug, request a feature, or share what delighted you. The feedback form opens your email client with a pre-filled message to support.",
    href: "/feedback",
    cta: "Send feedback",
    external: false,
  },
] as const;

export default function HelpContactPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="text-center">
          <p className="rtas-eyebrow">
            <Link href="/help" className="text-ds-accent-lavender">
              Help Center
            </Link>{" "}
            · Contact
          </p>
          <h1 className="text-zinc-100">We&apos;re here to help</h1>
          <p className="mx-auto mt-3 max-w-xl text-ds-text-muted">
            Include your account email, what you were trying to do, and roughly when it
            happened. That helps us resolve issues faster.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <ButtonLink href={`mailto:${SITE_SUPPORT_EMAIL}`} variant="lavender">
              Email {SITE_SUPPORT_EMAIL}
            </ButtonLink>
            <ButtonLink href="/feedback" variant="primary">
              Send feedback
            </ButtonLink>
          </div>
        </InnerPageSection>

        <section className="grid gap-4 md:grid-cols-2" aria-labelledby="contact-channels">
          <h2 id="contact-channels" className="sr-only">
            Contact channels
          </h2>
          {CHANNELS.map((channel) => (
            <InnerPageSection key={channel.title}>
              <h3 className="text-lg text-zinc-100">{channel.title}</h3>
              <p className="mt-2 text-sm text-ds-text-muted">{channel.body}</p>
              <div className="mt-4">
                {channel.external ? (
                  <a
                    href={channel.href}
                    className="rtas-btn-ghost rtas-ui-btn"
                    {...(channel.href.startsWith("http")
                      ? { target: "_blank", rel: "noopener noreferrer" }
                      : {})}
                  >
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

        <InnerPageSection className="text-center">
          <h2 className="text-xl text-zinc-100">Before you write</h2>
          <p className="mx-auto mt-2 max-w-xl text-sm text-ds-text-muted">
            Check Troubleshooting for common render and sign-in fixes, Billing for credits
            and downloads, and Status if you suspect a platform outage.
          </p>
          <div className="mt-5 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/help/troubleshooting" variant="ghost">
              Troubleshooting
            </ButtonLink>
            <ButtonLink href="/help/billing" variant="ghost">
              Billing
            </ButtonLink>
            <ButtonLink href="/status" variant="ghost">
              System status
            </ButtonLink>
          </div>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
