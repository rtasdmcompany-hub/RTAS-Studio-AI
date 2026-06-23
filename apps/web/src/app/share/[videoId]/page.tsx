import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { PRODUCT_NAME } from "@rtas/shared";
import { SharePublicView } from "@/components/SharePublicView";
import { getPublicShare } from "@/lib/server/share-store";

type PageProps = {
  params: { videoId: string };
};

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const share = await getPublicShare(params.videoId);
  if (!share) {
    return { title: `Video not found · ${PRODUCT_NAME}` };
  }

  return {
    title: `${share.title} · ${PRODUCT_NAME}`,
    description:
      share.prompt?.slice(0, 160) ??
      `Watch an AI video created with ${PRODUCT_NAME}.`,
    openGraph: {
      title: share.title,
      description: share.prompt?.slice(0, 160) ?? `Created with ${PRODUCT_NAME}`,
      type: "video.other",
    },
  };
}

export default async function ShareVideoPage({ params }: PageProps) {
  const share = await getPublicShare(params.videoId);
  if (!share) {
    notFound();
  }

  return <SharePublicView share={share} />;
}
