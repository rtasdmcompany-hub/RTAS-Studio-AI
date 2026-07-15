import type { Metadata } from "next";
import { PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";

export const metadata: Metadata = {
  title: "Blog",
  description: `Product stories, pricing guides, and workflow tips from ${PRODUCT_NAME} for international creators and teams.`,
  openGraph: {
    title: `Blog · ${PRODUCT_NAME}`,
    description:
      "Guides on studio workflow, credits, commercial licensing, features, and shipping AI video.",
  },
};

const POSTS = [
  {
    title: "Studio workflow: compose → render → publish",
    category: "Product",
    readTime: "6 min read",
    body: "A practical walkthrough of the guided Studio path: choose mode and category, lock identity when you need a real face, confirm credit cost before generate, then preview and archive the master. This piece explains how identity lock, credits, and commercial downloads fit into one workspace for music videos, ads, and stories — without bouncing between disconnected tools.",
    href: "/how-to-use",
    cta: "Open How to use",
  },
  {
    title: "Plans that map to real output",
    category: "Pricing",
    readTime: "5 min read",
    body: "Creator Starter, Pro Studio, and Production Enterprise are packaged around what you actually ship: resolution caps, watermark policy, queue priority, and commercial rights. We break down when Pro is the default for weekly creators, when Enterprise unlocks cinematic 4K, and how Merchant of Record checkout handles tax and invoices internationally.",
    href: "/pricing",
    cta: "Compare pricing",
  },
  {
    title: "What shipped recently",
    category: "Changelog",
    readTime: "4 min read",
    body: "Release notes written for creators — UX polish in the wizard, clearer billing and credit surfaces, and reliability improvements across the render path. Use the changelog when you want a concise record of product changes without digging through engineering commits.",
    href: "/help/changelog",
    cta: "Read changelog",
  },
  {
    title: "Identity lock without the guesswork",
    category: "Features",
    readTime: "7 min read",
    body: "Real-face mode needs a clear reference and consent; Avatar and Cartoon keep continuity without a live likeness lock. We cover Style-step previews, when to switch modes mid-project, and how server-side credit guards keep generation honest. Pair this with the features matrix if you are choosing a plan for client work.",
    href: "/features",
    cta: "Explore features",
  },
  {
    title: "See the look before you buy credits",
    category: "Showcase",
    readTime: "3 min read",
    body: "The AI Showcase collects cinematic examples across categories so you can judge motion, lighting, and style before you spend credits. Use it as a briefing tool with clients or as a reference when picking a visual direction in Studio.",
    href: "/showcase",
    cta: "View showcase",
  },
  {
    title: "Credits, downloads, and commercial rights",
    category: "Docs",
    readTime: "5 min read",
    body: "One credit equals roughly one second of finished video. Watermarked previews stay available for evaluation; paid tiers unlock downloadable masters and commercial licensing. This article points to product documentation for billing, publishing, and the library dashboard so finance and creative stay aligned.",
    href: "/docs",
    cta: "Open documentation",
  },
  {
    title: "Shipping internationally with clear ops",
    category: "Operations",
    readTime: "4 min read",
    body: "For teams evaluating platform readiness: health and readiness probes, status surfaces, and developer notes on public BFF patterns. If you are integrating monitoring or reviewing share links for client review, start here and deepen in Developers.",
    href: "/developers",
    cta: "Developer notes",
  },
] as const;

export default function BlogPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="text-center">
          <p className="rtas-eyebrow">Blog</p>
          <h1 className="text-white">Updates from {PRODUCT_NAME}</h1>
          <p className="mx-auto mt-3 max-w-2xl text-ds-text-muted">
            Product stories, pricing clarity, workflow tips, and changelog highlights for
            international creators and teams — written as full guides you can act on today.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/help/changelog" variant="lavender">
              Latest changelog
            </ButtonLink>
            <ButtonLink href="/how-to-use" variant="ghost">
              Studio guide
            </ButtonLink>
          </div>
        </InnerPageSection>

        <section className="grid gap-4" aria-label="Articles">
          {POSTS.map((post) => (
            <InnerPageSection key={post.title}>
              <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                <p className="rtas-eyebrow">{post.category}</p>
                <p className="text-xs text-ds-text-muted">{post.readTime}</p>
              </div>
              <h2 className="text-xl text-white">{post.title}</h2>
              <p className="mt-2 text-sm leading-relaxed text-ds-text-muted">{post.body}</p>
              <div className="mt-4">
                <ButtonLink href={post.href} variant="ghost">
                  {post.cta} →
                </ButtonLink>
              </div>
            </InnerPageSection>
          ))}
        </section>

        <InnerPageSection className="text-center">
          <h2 className="text-xl text-white">Keep shipping</h2>
          <p className="mx-auto mt-2 max-w-xl text-sm text-ds-text-muted">
            For hands-on help, open How to use or Help Center. For plan decisions, compare
            pricing. For live platform health, check Status.
          </p>
          <div className="mt-5 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/help" variant="lavender">
              Help Center
            </ButtonLink>
            <ButtonLink href="/pricing" variant="ghost">
              Pricing
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
