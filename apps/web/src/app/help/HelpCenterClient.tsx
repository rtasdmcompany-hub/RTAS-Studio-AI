"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";
import {
  HELP_ARTICLES,
  HELP_CATEGORIES,
  searchHelpArticles,
  type HelpCategoryId,
} from "@/lib/customer-success/help-kb";

const HUB_EXTRAS = [
  { href: "/success", title: "Success Center", body: "Full customer success hub." },
  { href: "/tickets", title: "Support tickets", body: "Create and track tickets (sign-in)." },
  { href: "/feedback", title: "Feedback & surveys", body: "CSAT, NPS, bugs, and ideas." },
  { href: "/help/changelog", title: "Release notes", body: "What shipped recently." },
  { href: "/retention", title: "Retention Center", body: "Insights and milestones (sign-in)." },
  { href: "/status", title: "System status", body: "Live health probes." },
] as const;

export function HelpCenterClient() {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<HelpCategoryId | "all">("all");

  const results = useMemo(
    () => searchHelpArticles(query, category),
    [query, category]
  );

  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="text-center">
          <p className="rtas-eyebrow">Help Center</p>
          <h1 className="text-zinc-100">How can we help?</h1>
          <p className="mx-auto mt-3 max-w-2xl text-ds-text-muted">
            Search the knowledge base across Account, Billing, Credits, Video Generation,
            Templates, AI Models, Enterprise, API, Security, and Technical Issues.
          </p>
          <div className="mx-auto mt-8 max-w-xl text-left">
            <label className="block text-sm">
              <span className="sr-only">Search help</span>
              <input
                type="search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search articles…"
                className="w-full rounded-lg border border-ds-border bg-ds-surface px-4 py-3 text-ds-text"
              />
            </label>
          </div>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/tickets" variant="lavender">
              Open a ticket
            </ButtonLink>
            <ButtonLink href="/success" variant="ghost">
              Success Center
            </ButtonLink>
            <ButtonLink href="/help/contact" variant="ghost">
              Contact
            </ButtonLink>
          </div>
        </InnerPageSection>

        <InnerPageSection aria-labelledby="help-cats">
          <h2 id="help-cats" className="text-xl text-zinc-100">
            Categories
          </h2>
          <div className="mt-4 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setCategory("all")}
              className={`rounded-lg border px-3 py-1.5 text-sm ${
                category === "all"
                  ? "border-ds-accent-lavender text-zinc-100"
                  : "border-ds-border text-ds-text-muted"
              }`}
            >
              All ({HELP_ARTICLES.length})
            </button>
            {HELP_CATEGORIES.map((c) => (
              <button
                key={c.id}
                type="button"
                onClick={() => setCategory(c.id)}
                className={`rounded-lg border px-3 py-1.5 text-sm ${
                  category === c.id
                    ? "border-ds-accent-lavender text-zinc-100"
                    : "border-ds-border text-ds-text-muted"
                }`}
              >
                {c.label}
              </button>
            ))}
          </div>
          <div className="mt-6 grid gap-3 md:grid-cols-2">
            {HELP_CATEGORIES.map((c) => (
              <button
                key={`card-${c.id}`}
                type="button"
                onClick={() => setCategory(c.id)}
                className="inner-page-section text-left transition hover:border-ds-accent-lavender/40"
              >
                <h3 className="text-lg text-zinc-100">{c.label}</h3>
                <p className="mt-2 text-sm text-ds-text-muted">{c.description}</p>
              </button>
            ))}
          </div>
        </InnerPageSection>

        <InnerPageSection aria-labelledby="help-results">
          <h2 id="help-results" className="text-xl text-zinc-100">
            {query.trim() ? `Results (${results.length})` : "Articles"}
          </h2>
          {results.length === 0 ? (
            <p className="mt-4 text-sm text-ds-text-muted">
              No articles match. Try another term or{" "}
              <Link href="/tickets" className="text-ds-accent-lavender underline-offset-2 hover:underline">
                open a support ticket
              </Link>
              .
            </p>
          ) : (
            <dl className="mt-6 space-y-6 text-left">
              {results.map((item) => (
                <div key={item.id}>
                  <dt className="font-medium text-zinc-100">
                    <span className="text-xs uppercase tracking-wide text-ds-text-muted">
                      {HELP_CATEGORIES.find((c) => c.id === item.category)?.label} ·{" "}
                    </span>
                    {item.title}
                  </dt>
                  <dd className="mt-2 text-sm text-ds-text-muted">
                    {item.body}
                    {item.href ? (
                      <>
                        {" "}
                        <Link
                          href={item.href}
                          className="text-ds-accent-lavender underline-offset-2 hover:underline"
                        >
                          Learn more →
                        </Link>
                      </>
                    ) : null}
                  </dd>
                </div>
              ))}
            </dl>
          )}
        </InnerPageSection>

        <section aria-labelledby="help-extras" className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <h2 id="help-extras" className="sr-only">
            Related surfaces
          </h2>
          {HUB_EXTRAS.map((t) => (
            <Link
              key={t.href}
              href={t.href}
              className="inner-page-section block transition hover:border-ds-accent-lavender/40"
            >
              <h3 className="text-lg text-zinc-100">{t.title}</h3>
              <p className="mt-2 text-sm text-ds-text-muted">{t.body}</p>
            </Link>
          ))}
        </section>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
