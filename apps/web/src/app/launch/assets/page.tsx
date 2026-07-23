import type { Metadata } from "next";
import { PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";
import { buildPageMetadata } from "@/lib/site-metadata";
import { ASSET_KIND_LABEL, LAUNCH_ASSETS } from "@/lib/launch/assets";

export const metadata: Metadata = buildPageMetadata({
  title: "Launch Asset Library",
  description: `Download center for ${PRODUCT_NAME} logos, demos, media kit, founder bio, and brand guidelines. Placeholders are labeled — no fake press assets.`,
  path: "/launch/assets",
  openGraphTitle: `Asset Library · ${PRODUCT_NAME}`,
});

export default function LaunchAssetsPage() {
  const ready = LAUNCH_ASSETS.filter((a) => !a.placeholder && a.href);
  const placeholders = LAUNCH_ASSETS.filter((a) => a.placeholder || !a.href);

  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="text-center">
          <p className="rtas-eyebrow">Press & brand</p>
          <h1 className="text-zinc-100">Launch Asset Library</h1>
          <p className="mx-auto mt-3 max-w-2xl text-ds-text-muted">
            Logos, demos, and kit references for launch partners. Missing files are labeled
            Placeholder — we do not invent screenshots or fabricated media kits.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/launch" variant="ghost">
              Launch Center
            </ButtonLink>
            <ButtonLink href="/showcase" variant="lavender">
              Showcase
            </ButtonLink>
            <ButtonLink href="/about" variant="ghost">
              About
            </ButtonLink>
          </div>
        </InnerPageSection>

        <InnerPageSection>
          <h2 className="text-xl text-zinc-100">Available now</h2>
          <ul className="mt-6 space-y-4">
            {ready.map((asset) => (
              <li
                key={asset.id}
                className="flex flex-col gap-2 border-b border-white/10 pb-4 sm:flex-row sm:items-center sm:justify-between"
              >
                <div>
                  <p className="text-xs uppercase tracking-wide text-ds-text-muted">
                    {ASSET_KIND_LABEL[asset.kind]}
                  </p>
                  <p className="text-zinc-100">{asset.title}</p>
                  <p className="text-sm text-ds-text-muted">{asset.notes}</p>
                </div>
                {asset.href ? (
                  <ButtonLink href={asset.href} variant="ghost">
                    Open
                  </ButtonLink>
                ) : null}
              </li>
            ))}
          </ul>
        </InnerPageSection>

        <InnerPageSection>
          <h2 className="text-xl text-zinc-100">Placeholders / docs</h2>
          <ul className="mt-6 space-y-4">
            {placeholders.map((asset) => (
              <li key={asset.id} className="border-b border-white/10 pb-4">
                <p className="text-xs uppercase tracking-wide text-ds-text-muted">
                  {ASSET_KIND_LABEL[asset.kind]}
                  {asset.placeholder ? " · Placeholder" : ""}
                </p>
                <p className="text-zinc-100">{asset.title}</p>
                <p className="text-sm text-ds-text-muted">{asset.notes}</p>
                {asset.href ? (
                  <p className="mt-2">
                    <ButtonLink href={asset.href} variant="ghost">
                      Open reference
                    </ButtonLink>
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        </InnerPageSection>

        <InnerPageSection className="inner-page-section--panel text-center">
          <h2 className="text-lg text-zinc-100">Brand guidelines</h2>
          <p className="mx-auto mt-2 max-w-xl text-sm text-ds-text-muted">
            Verified tokens live in the design system. Enterprise brand guide (Verified vs
            Proposed) is in the repo at marketing/enterprise-brand-guide.md. Press process:
            docs/launch/PRESS_KIT_GUIDE.md.
          </p>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
