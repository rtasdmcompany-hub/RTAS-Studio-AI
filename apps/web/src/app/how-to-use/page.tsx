import type { Metadata } from "next";
import { PRODUCT_NAME } from "@rtas/shared";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import { HowToUseGuide } from "@/components/marketing/HowToUseGuide";

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
