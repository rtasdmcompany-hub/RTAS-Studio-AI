"use client";

import dynamic from "next/dynamic";
import { StudioSkeleton } from "@/components/ui/skeletons";
import { StudioChromeFooter } from "@/components/marketing/StudioChromeFooter";

const StudioClient = dynamic(
  () => import("./StudioClient").then((mod) => mod.StudioClient),
  {
    ssr: false,
    loading: () => <StudioSkeleton />,
  }
);

const LiveChatWidget = dynamic(
  () =>
    import("@/components/marketing/LiveChatWidget").then(
      (mod) => mod.LiveChatWidget
    ),
  { ssr: false }
);

const BackToTop = dynamic(
  () =>
    import("@/components/marketing/BackToTop").then((mod) => mod.BackToTop),
  { ssr: false }
);

export function StudioShell() {
  return (
    <div className="studio-shell--unified">
      <div className="studio-shell__main">
        <StudioClient />
      </div>
      <StudioChromeFooter />
      <BackToTop />
      <LiveChatWidget />
    </div>
  );
}
