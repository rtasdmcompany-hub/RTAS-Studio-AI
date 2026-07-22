import type { Metadata } from "next";
import Link from "next/link";
import { PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";
import { PRODUCT_VERSION, RELEASE_NOTES } from "@/lib/release-notes";
import { buildPageMetadata } from "@/lib/site-metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Release Notes",
  description: `Release notes for ${PRODUCT_NAME} v${PRODUCT_VERSION} — features, improvements, bug fixes, and known issues.`,
  path: "/help/changelog",
  openGraphTitle: `Release Notes · Help · ${PRODUCT_NAME}`,
});

function NoteList({ title, items }: { title: string; items?: string[] }) {
  if (!items?.length) return null;
  return (
    <div className="mt-4">
      <h3 className="text-sm font-medium uppercase tracking-wide text-ds-text-muted">
        {title}
      </h3>
      <ul className="mt-2 list-disc space-y-1.5 pl-5 text-sm text-ds-text-muted">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

export default function HelpChangelogPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection>
          <p className="rtas-eyebrow">
            <Link href="/help" className="text-ds-accent-lavender">
              Customer Success
            </Link>{" "}
            · Release Notes
          </p>
          <h1 className="text-zinc-100">What&apos;s new</h1>
          <p className="mt-3 max-w-2xl text-ds-text-muted">
            Structured notes from the real product version ({PRODUCT_VERSION}). We do not invent
            release history — only published engineering changelog entries appear here.
          </p>
        </InnerPageSection>

        <div className="grid gap-4">
          {RELEASE_NOTES.map((release) => (
            <InnerPageSection key={release.version} aria-labelledby={`rel-${release.version}`}>
              <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                <h2 id={`rel-${release.version}`} className="text-lg text-zinc-100">
                  Version {release.version}
                </h2>
                <time className="text-sm text-ds-text-muted" dateTime={release.date}>
                  {release.date}
                </time>
                {release.codename ? (
                  <span className="text-sm text-ds-text-muted">{release.codename}</span>
                ) : null}
              </div>
              {release.build ? (
                <p className="mt-1 text-xs text-ds-text-muted">Build {release.build}</p>
              ) : null}
              <p className="mt-3 text-sm text-ds-text-muted">{release.summary}</p>
              <NoteList title="Features" items={release.sections.features} />
              <NoteList title="Improvements" items={release.sections.improvements} />
              <NoteList title="Security" items={release.sections.security} />
              <NoteList title="Bug Fixes" items={release.sections.bugFixes} />
              <NoteList title="Known Issues" items={release.sections.knownIssues} />
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
          <ButtonLink href="/beta" variant="ghost" className="ml-3">
            Public beta
          </ButtonLink>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
