import type { Metadata } from "next";
import { BRAND_FAVICON_PATH } from "@/lib/brand-assets";
import { SITE_URL, canonicalUrl } from "@/lib/site-url";

/** Default document title for global search indexing. */
export const SITE_METADATA_TITLE =
  "RTAS Studio AI — International AI Video Studio | Music Videos & Commercials";

/** Default meta description aligned with international positioning. */
export const SITE_METADATA_DESCRIPTION =
  "Compose, render, and publish cinematic AI videos with Authorized Identity Preservation for content you own. Transparent credits (1 credit = 1 second), global checkout, and a single studio for artists, brands, and agencies.";

export const SITE_METADATA_KEYWORDS = [
  "AI video studio",
  "AI music video",
  "identity preservation video",
  "cinematic AI video",
  "text to video",
  "RTAS Studio AI",
  "AI video generator",
  "commercial AI video",
] as const;

/** Social / Open Graph image (absolute). Must be raster for social platforms. */
export const SITE_OG_IMAGE_PATH = "/og-image.png";
export const SITE_OG_IMAGE_URL = `${SITE_URL}${SITE_OG_IMAGE_PATH}`;
export const SITE_OG_IMAGE_WIDTH = 1200;
export const SITE_OG_IMAGE_HEIGHT = 630;

export const SITE_METADATA_ICONS: NonNullable<Metadata["icons"]> = {
  icon: [{ url: BRAND_FAVICON_PATH, type: "image/png" }],
  shortcut: [{ url: BRAND_FAVICON_PATH, type: "image/png" }],
  apple: [{ url: BRAND_FAVICON_PATH, type: "image/png" }],
};

export const SITE_MANIFEST = "/site.webmanifest";

const sharedOpenGraph: Metadata["openGraph"] = {
  type: "website",
  locale: "en_US",
  siteName: "RTAS Studio AI",
  images: [
    {
      url: SITE_OG_IMAGE_URL,
      width: SITE_OG_IMAGE_WIDTH,
      height: SITE_OG_IMAGE_HEIGHT,
      alt: "RTAS Studio AI — International AI Video Studio",
    },
  ],
};

const sharedTwitter: Metadata["twitter"] = {
  card: "summary_large_image",
  site: "@RTASDigital",
  creator: "@RTASDigital",
  images: [SITE_OG_IMAGE_URL],
};

export const rootMetadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: SITE_METADATA_TITLE,
    template: "%s | RTAS Studio AI",
  },
  description: SITE_METADATA_DESCRIPTION,
  keywords: [...SITE_METADATA_KEYWORDS],
  icons: SITE_METADATA_ICONS,
  manifest: SITE_MANIFEST,
  alternates: {
    canonical: "/",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-image-preview": "large",
      "max-snippet": -1,
      "max-video-preview": -1,
    },
  },
  verification: {
    google: process.env.NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION || undefined,
    yandex: undefined,
    other: {
      ...(process.env.NEXT_PUBLIC_BING_SITE_VERIFICATION
        ? { "msvalidate.01": process.env.NEXT_PUBLIC_BING_SITE_VERIFICATION }
        : {}),
    },
  },
  openGraph: {
    ...sharedOpenGraph,
    title: SITE_METADATA_TITLE,
    description: SITE_METADATA_DESCRIPTION,
    url: SITE_URL,
  },
  twitter: {
    ...sharedTwitter,
    title: SITE_METADATA_TITLE,
    description: SITE_METADATA_DESCRIPTION,
  },
  category: "technology",
};

export type PageMetadataInput = {
  title: string;
  description: string;
  /** Path only, e.g. `/pricing` */
  path: string;
  openGraphTitle?: string;
  openGraphDescription?: string;
  noIndex?: boolean;
};

/** Consistent per-page SEO metadata with canonical, OG, and Twitter tags. */
export function buildPageMetadata(input: PageMetadataInput): Metadata {
  const canonical = input.path.startsWith("/") ? input.path : `/${input.path}`;
  const ogTitle = input.openGraphTitle ?? input.title;
  const ogDescription = input.openGraphDescription ?? input.description;

  return {
    title: input.title,
    description: input.description,
    alternates: {
      canonical,
    },
    robots: input.noIndex
      ? { index: false, follow: false }
      : {
          index: true,
          follow: true,
        },
    openGraph: {
      ...sharedOpenGraph,
      title: ogTitle,
      description: ogDescription,
      url: canonicalUrl(canonical),
    },
    twitter: {
      ...sharedTwitter,
      title: ogTitle,
      description: ogDescription,
    },
  };
}
