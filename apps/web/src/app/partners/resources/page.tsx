import type { Metadata } from "next";
import Link from "next/link";
import { PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";
import { buildPageMetadata } from "@/lib/site-metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Marketing Resources Center",
  description: `Brand assets and partner marketing materials for ${PRODUCT_NAME}. Real assets linked where they exist; placeholders labeled honestly where missing.`,
  path: "/partners/resources",
  openGraphTitle: `Marketing Resources · ${PRODUCT_NAME}`,
  openGraphDescription:
    "Logos, brand guidelines, screenshots, videos, banners, social kit, and email templates for RTAS partners and affiliates.",
});

type ResourceItem = {
  title: string;
  status: "available" | "placeholder";
  href?: string;
  note: string;
};

const SECTIONS: Array<{ id: string; title: string; items: ResourceItem[] }> = [
  {
    id: "logos",
    title: "Logos",
    items: [
      {
        title: "Primary logo (SVG)",
        status: "available",
        href: "/logo.svg",
        note: "Public web logo.",
      },
      {
        title: "RTAS Group logo",
        status: "available",
        href: "/rtas-group-logo.png",
        note: "Group mark for operator attribution contexts.",
      },
      {
        title: "Light-mode logo lockups",
        status: "placeholder",
        note: "Proposed in brand guidelines — not packaged as a download yet.",
      },
    ],
  },
  {
    id: "guidelines",
    title: "Brand guidelines",
    items: [
      {
        title: "Brand guidelines (docs)",
        status: "available",
        href: "https://github.com/rtasdmcompany-hub/RTAS-Studio-AI/blob/main/docs/branding/BRAND_GUIDELINES.md",
        note: "Canonical brand system documentation in the repository.",
      },
      {
        title: "Enterprise brand guide",
        status: "available",
        href: "https://github.com/rtasdmcompany-hub/RTAS-Studio-AI/blob/main/marketing/enterprise-brand-guide.md",
        note: "Phase 13 enterprise brand guide.",
      },
      {
        title: "Branding asset index",
        status: "available",
        href: "https://github.com/rtasdmcompany-hub/RTAS-Studio-AI/blob/main/business/branding/README.md",
        note: "Index of live public assets and formal docs.",
      },
    ],
  },
  {
    id: "screenshots",
    title: "Screenshots",
    items: [
      {
        title: "Open Graph / social share image",
        status: "available",
        href: "/og-image.png",
        note: "Default OG raster for social platforms.",
      },
      {
        title: "Studio UI screenshot pack",
        status: "placeholder",
        note: "Curated, rights-cleared UI pack not published yet — do not invent screenshots.",
      },
    ],
  },
  {
    id: "videos",
    title: "Videos",
    items: [
      {
        title: "Showcase videos",
        status: "available",
        href: "/showcase",
        note: "Public showcase page and /public/showcase/*.mp4 assets.",
      },
      {
        title: "Partner-ready edit packages",
        status: "placeholder",
        note: "Edited cutdowns with partner end-cards not shipped yet.",
      },
    ],
  },
  {
    id: "banners",
    title: "Banners",
    items: [
      {
        title: "Web / display banner set",
        status: "placeholder",
        note: "Sized banner kit (728×90, 300×250, etc.) not designed yet.",
      },
    ],
  },
  {
    id: "social",
    title: "Social kit",
    items: [
      {
        title: "Social profile links",
        status: "available",
        href: "/about",
        note: "Official RTAS Digital channels listed on site chrome / about.",
      },
      {
        title: "Social post templates (Canva/Figma)",
        status: "placeholder",
        note: "Template pack not published — use messaging framework until then.",
      },
    ],
  },
  {
    id: "email",
    title: "Email templates",
    items: [
      {
        title: "Affiliate intro email (copy outline)",
        status: "placeholder",
        note: "Outline lives in docs/partners/MARKETING_RESOURCES.md — no live HTML blast kit.",
      },
      {
        title: "Product email marketing system (internal)",
        status: "available",
        href: "https://github.com/rtasdmcompany-hub/RTAS-Studio-AI/blob/main/docs/marketing/EMAIL_MARKETING_SYSTEM.md",
        note: "Internal strategy doc — not a customer-facing send.",
      },
    ],
  },
];

export default function PartnerResourcesPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="text-center">
          <p className="rtas-eyebrow">Partners · Affiliates</p>
          <h1 className="text-zinc-100">Marketing Resources Center</h1>
          <p className="mx-auto mt-3 max-w-2xl text-ds-text-muted">
            Structure for logos, brand guidelines, screenshots, videos, banners, social kit, and
            email templates. Available assets link to real files or docs; missing items are labeled
            placeholders — never fabricated downloads.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/affiliate" variant="lavender">
              Affiliate program
            </ButtonLink>
            <ButtonLink href="/partners" variant="ghost">
              Partners
            </ButtonLink>
            <ButtonLink href="/showcase" variant="ghost">
              Showcase
            </ButtonLink>
          </div>
        </InnerPageSection>

        {SECTIONS.map((section) => (
          <InnerPageSection key={section.id} aria-labelledby={`res-${section.id}`}>
            <h2 id={`res-${section.id}`} className="text-xl text-zinc-100">
              {section.title}
            </h2>
            <ul className="mt-4 space-y-3">
              {section.items.map((item) => (
                <li
                  key={item.title}
                  className="flex flex-col gap-1 border-b border-white/5 pb-3 last:border-0 sm:flex-row sm:items-start sm:justify-between sm:gap-6"
                >
                  <div>
                    <p className="font-medium text-zinc-100">{item.title}</p>
                    <p className="mt-1 text-sm text-ds-text-muted">{item.note}</p>
                  </div>
                  <div className="shrink-0 text-sm">
                    {item.status === "available" && item.href ? (
                      item.href.startsWith("http") ? (
                        <a
                          href={item.href}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-ds-accent-lavender underline-offset-2 hover:underline"
                        >
                          Open
                        </a>
                      ) : (
                        <Link
                          href={item.href}
                          className="text-ds-accent-lavender underline-offset-2 hover:underline"
                        >
                          Open
                        </Link>
                      )
                    ) : (
                      <span className="text-amber-200/80">Placeholder — not available yet</span>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </InnerPageSection>
        ))}

        <InnerPageSection className="text-center">
          <p className="text-sm text-ds-text-muted">
            Repository docs:{" "}
            <code className="text-zinc-300">docs/partners/MARKETING_RESOURCES.md</code> ·{" "}
            <code className="text-zinc-300">docs/branding/</code> ·{" "}
            <code className="text-zinc-300">marketing/</code>
          </p>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
