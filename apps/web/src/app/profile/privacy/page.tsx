import type { Metadata } from "next";
import { PrivacySettingsClient } from "@/components/profile/PrivacySettingsClient";
import { buildPageMetadata } from "@/lib/site-metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Privacy settings",
  description:
    "Download personal data, manage cookie and email preferences, or request account deletion.",
  path: "/profile/privacy",
  noIndex: true,
});

export default function ProfilePrivacyPage() {
  return <PrivacySettingsClient />;
}
