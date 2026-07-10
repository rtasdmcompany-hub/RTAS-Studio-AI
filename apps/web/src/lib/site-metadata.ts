import type { Metadata } from "next";
import { BRAND_FAVICON_PATH } from "@/lib/brand-assets";

/** Default document title for global search indexing. */
export const SITE_METADATA_TITLE =
  "RTAS Studio AI — International AI Video Studio | Identity-Locked Music Videos";

/** Default meta description aligned with international positioning. */
export const SITE_METADATA_DESCRIPTION =
  "Compose, render, and publish cinematic AI videos with identity lock. Transparent credits (1 credit = 1 second), global checkout, and a single studio for artists, brands, and agencies.";

export const SITE_METADATA_ICONS: NonNullable<Metadata["icons"]> = {
  icon: [{ url: BRAND_FAVICON_PATH, type: "image/png" }],
  shortcut: [{ url: BRAND_FAVICON_PATH, type: "image/png" }],
  apple: [{ url: BRAND_FAVICON_PATH, type: "image/png" }],
};

export const rootMetadata: Metadata = {
  title: {
    default: SITE_METADATA_TITLE,
    template: "%s | RTAS Studio AI",
  },
  description: SITE_METADATA_DESCRIPTION,
  icons: SITE_METADATA_ICONS,
};
