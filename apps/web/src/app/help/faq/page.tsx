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
import { HELP_ARTICLES, HELP_CATEGORIES } from "@/lib/customer-success/help-kb";
import { buildPageMetadata } from "@/lib/site-metadata";
import { breadcrumbSchema, faqSchema } from "@/lib/structured-data";

export const metadata: Metadata = buildPageMetadata({
  title: "FAQ",
  description: `Categorized FAQ for ${PRODUCT_NAME}: Account, Billing, Credits, Video Generation, Templates, AI Models, Enterprise, API, Security, and Technical Issues.`,
  path: "/help/faq",
  openGraphTitle: `FAQ · Help · ${PRODUCT_NAME}`,
});

export default function HelpFaqPage() {
  return (
    <MarketingLayout>
      <StructuredData
        data={[
          breadcrumbSchema([
            { name: "Home", path: "/" },
            { name: "Help", path: "/help" },
            { name: "FAQ", path: "/help/faq" },
          ]),
          faqSchema(
            HELP_ARTICLES.map((item) => ({
              question: item.title,
              answer: item.body,
            }))
          ),
        ]}
      />
      <InnerPageContainer>
        <InnerPageSection>
          <p className="rtas-eyebrow">
            <Link href="/help" className="text-ds-accent-lavender">
              Help Center
            </Link>{" "}
            · FAQ
          </p>
          <h1 className="text-zinc-100">Common questions by category</h1>
          <p className="mt-3 max-w-2xl text-ds-text-muted">
            Clear answers for first-time creators and returning teams. Use Help search for
            keyword lookup.
          </p>
        </InnerPageSection>

        {HELP_CATEGORIES.map((cat) => {
          const items = HELP_ARTICLES.filter((a) => a.category === cat.id);
          if (!items.length) return null;
          return (
            <InnerPageSection key={cat.id} aria-labelledby={`faq-${cat.id}`}>
              <h2 id={`faq-${cat.id}`} className="text-xl text-zinc-100">
                {cat.label}
              </h2>
              <p className="mt-1 text-sm text-ds-text-muted">{cat.description}</p>
              <dl className="mt-6 space-y-6 text-left">
                {items.map((item) => (
                  <div key={item.id}>
                    <dt className="font-medium text-zinc-100">{item.title}</dt>
                    <dd className="mt-2 text-sm text-ds-text-muted">{item.body}</dd>
                  </div>
                ))}
              </dl>
            </InnerPageSection>
          );
        })}

        <InnerPageSection className="text-center">
          <ButtonLink href="/tickets" variant="primary">
            Open a support ticket
          </ButtonLink>
          <ButtonLink href="/help" variant="ghost" className="ml-3">
            Search Help
          </ButtonLink>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
