import type { Metadata } from "next";
import { BRAND_FAVICON_PATH } from "@/lib/brand-assets";

/** Default document title for global search indexing. */
export const SITE_METADATA_TITLE =
  "RTAS Studio AI - International AI Video Studio";

/** Default meta description aligned with international positioning. */
export const SITE_METADATA_DESCRIPTION =
  "RTAS Studio AI is the international AI video studio for cinematic music videos, identity-locked faces, and scroll-stopping content — compose, render, and publish in one workspace.";

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
