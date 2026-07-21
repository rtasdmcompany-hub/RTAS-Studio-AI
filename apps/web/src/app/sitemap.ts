import type { MetadataRoute } from "next";

const CANONICAL = "https://rtasstudio.com";

/** Public marketing & support pages eligible for search indexing. */
const INDEXABLE_PATHS: Array<{
  path: string;
  changeFrequency: MetadataRoute.Sitemap[number]["changeFrequency"];
  priority: number;
}> = [
  { path: "/", changeFrequency: "weekly", priority: 1 },
  { path: "/features", changeFrequency: "weekly", priority: 0.9 },
  { path: "/pricing", changeFrequency: "weekly", priority: 0.9 },
  { path: "/showcase", changeFrequency: "weekly", priority: 0.85 },
  { path: "/how-to-use", changeFrequency: "monthly", priority: 0.85 },
  { path: "/about", changeFrequency: "monthly", priority: 0.7 },
  { path: "/developers", changeFrequency: "monthly", priority: 0.7 },
  { path: "/docs", changeFrequency: "monthly", priority: 0.75 },
  { path: "/blog", changeFrequency: "weekly", priority: 0.65 },
  { path: "/careers", changeFrequency: "monthly", priority: 0.55 },
  { path: "/help", changeFrequency: "monthly", priority: 0.7 },
  { path: "/help/faq", changeFrequency: "monthly", priority: 0.7 },
  { path: "/help/contact", changeFrequency: "monthly", priority: 0.65 },
  { path: "/help/billing", changeFrequency: "monthly", priority: 0.6 },
  { path: "/help/changelog", changeFrequency: "weekly", priority: 0.55 },
  { path: "/help/troubleshooting", changeFrequency: "monthly", priority: 0.6 },
  { path: "/status", changeFrequency: "daily", priority: 0.5 },
  { path: "/privacy", changeFrequency: "yearly", priority: 0.4 },
  { path: "/terms", changeFrequency: "yearly", priority: 0.4 },
  { path: "/refund", changeFrequency: "yearly", priority: 0.4 },
  { path: "/cookies", changeFrequency: "yearly", priority: 0.35 },
  { path: "/feedback", changeFrequency: "yearly", priority: 0.3 },
];

export default function sitemap(): MetadataRoute.Sitemap {
  const lastModified = new Date();
  return INDEXABLE_PATHS.map(({ path, changeFrequency, priority }) => ({
    url: `${CANONICAL}${path === "/" ? "" : path}`,
    lastModified,
    changeFrequency,
    priority,
  }));
}
