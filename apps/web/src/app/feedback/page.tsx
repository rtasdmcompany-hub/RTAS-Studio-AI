import type { Metadata } from "next";
import { PRODUCT_NAME } from "@rtas/shared";
import { FeedbackClient } from "./FeedbackClient";

import { buildPageMetadata } from "@/lib/site-metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Feedback, CSAT & NPS",
  description: `Send bug reports, feature requests, suggestions, CSAT (1–5), and NPS (0–10) for ${PRODUCT_NAME}. Stored securely when submitted — no fabricated scores.`,
  path: "/feedback",
  openGraphTitle: `Feedback · ${PRODUCT_NAME}`,
});

export default function FeedbackPage() {
  return <FeedbackClient />;
}
