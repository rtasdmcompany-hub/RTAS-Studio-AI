import type { Metadata } from "next";
import { NotificationPrefsClient } from "@/components/profile/NotificationPrefsClient";
import { buildPageMetadata } from "@/lib/site-metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Notification preferences",
  description: "Manage email and in-app notification preferences for RTAS Studio AI.",
  path: "/profile/notifications",
  noIndex: true,
});

export default function NotificationPrefsPage() {
  return <NotificationPrefsClient />;
}
