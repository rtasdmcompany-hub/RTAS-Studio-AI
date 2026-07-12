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
  description: `News and product updates from ${PRODUCT_NAME}.`,
};

const POSTS = [
  {
    title: "Studio workflow: compose → render → publish",
    date: "Product",
    body: "How identity lock, credits, and commercial downloads fit into one guided studio for music videos, ads, and stories.",
    href: "/how-to-use",
  },
  {
    title: "Plans that map to real output",
    date: "Pricing",
    body: "Creator Starter, Pro Studio, and Production Enterprise — resolution, watermark, and commercial rights explained side by side.",
    href: "/pricing",
  },
  {
    title: "What shipped recently",
    date: "Changelog",
    body: "Release notes for creators — UX polish, billing clarity, and studio reliability improvements.",
    href: "/help/changelog",
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
            Product stories, pricing clarity, and changelog highlights for international creators
            and teams.
          </p>
        </InnerPageSection>

        <section className="grid gap-4" aria-label="Articles">
          {POSTS.map((post) => (
            <InnerPageSection key={post.title}>
              <p className="rtas-eyebrow">{post.date}</p>
              <h2 className="text-xl text-white">{post.title}</h2>
              <p className="mt-2 text-sm text-ds-text-muted">{post.body}</p>
              <div className="mt-4">
                <ButtonLink href={post.href} variant="ghost">
                  Read →
                </ButtonLink>
              </div>
            </InnerPageSection>
          ))}
        </section>

        <InnerPageSection className="text-center">
          <h2 className="text-xl text-white">Follow along</h2>
          <p className="mx-auto mt-2 max-w-xl text-sm text-ds-text-muted">
            For the latest ship notes, open the changelog. For hands-on help, use How to use or Help
            Center.
          </p>
          <div className="mt-5 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/help/changelog" variant="lavender">
              Changelog
            </ButtonLink>
            <ButtonLink href="/showcase" variant="ghost">
              AI Showcase
            </ButtonLink>
          </div>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
