import type { Metadata } from "next";
import dynamic from "next/dynamic";
import { PRODUCT_NAME } from "@rtas/shared";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";

const HowToUseGuide = dynamic(
  () =>
    import("@/components/marketing/HowToUseGuide").then(
      (mod) => mod.HowToUseGuide
    ),
  {
    loading: () => (
      <div className="inner-page-container max-w-6xl mx-auto px-4 pt-28 pb-16">
        <div className="rtas-ui-loading-overlay" role="status" aria-live="polite">
          Loading guide…
        </div>
      </div>
    ),
  }
);

export const metadata: Metadata = {
  title: `How to Use | ${PRODUCT_NAME}`,
  description:
    "Complete visual guide for RTAS Studio AI — Song, Religious, Cartoon, Podcast, Business, and Story videos step by step.",
};

export default function HowToUsePage() {
  return (
    <MarketingLayout>
      <HowToUseGuide />
    </MarketingLayout>
  );
}
