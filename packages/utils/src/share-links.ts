import { PRODUCT_NAME } from "@rtas/shared";

export function buildPublicSharePath(videoId: string): string {
  return `/share/${encodeURIComponent(videoId)}`;
}

export function buildPublicShareUrl(videoId: string, origin?: string): string {
  const base =
    origin ??
    (typeof window !== "undefined" ? window.location.origin : "");
  return `${base}${buildPublicSharePath(videoId)}`;
}

export function buildShareMessage(title: string): string {
  return `Watch "${title}" — created with ${PRODUCT_NAME}`;
}

export function buildWhatsAppShareUrl(publicUrl: string, title: string): string {
  const text = `${buildShareMessage(title)} ${publicUrl}`;
  return `https://wa.me/?text=${encodeURIComponent(text)}`;
}

export function buildTwitterShareUrl(publicUrl: string, title: string): string {
  const text = buildShareMessage(title);
  return `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(publicUrl)}`;
}

export function buildFacebookShareUrl(publicUrl: string): string {
  return `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(publicUrl)}`;
}

export function buildLinkedInShareUrl(publicUrl: string): string {
  return `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(publicUrl)}`;
}

export function buildRedditShareUrl(publicUrl: string, title: string): string {
  return `https://www.reddit.com/submit?url=${encodeURIComponent(publicUrl)}&title=${encodeURIComponent(buildShareMessage(title))}`;
}

export function buildEmailShareUrl(publicUrl: string, title: string): string {
  const subject = encodeURIComponent(`${PRODUCT_NAME}: ${title}`);
  const body = encodeURIComponent(`${buildShareMessage(title)}\n\n${publicUrl}`);
  return `mailto:?subject=${subject}&body=${body}`;
}

export function buildTelegramShareUrl(publicUrl: string, title: string): string {
  const text = `${buildShareMessage(title)}\n${publicUrl}`;
  return `https://t.me/share/url?url=${encodeURIComponent(publicUrl)}&text=${encodeURIComponent(text)}`;
}

export function buildPinterestShareUrl(publicUrl: string, title: string): string {
  return `https://www.pinterest.com/pin/create/button/?url=${encodeURIComponent(publicUrl)}&description=${encodeURIComponent(buildShareMessage(title))}`;
}

export type SocialShareChannel =
  | "x"
  | "facebook"
  | "linkedin"
  | "whatsapp"
  | "telegram"
  | "reddit"
  | "email"
  | "pinterest";

export function buildSocialShareUrl(
  channel: SocialShareChannel,
  publicUrl: string,
  title: string
): string {
  switch (channel) {
    case "x":
      return buildTwitterShareUrl(publicUrl, title);
    case "facebook":
      return buildFacebookShareUrl(publicUrl);
    case "linkedin":
      return buildLinkedInShareUrl(publicUrl);
    case "whatsapp":
      return buildWhatsAppShareUrl(publicUrl, title);
    case "telegram":
      return buildTelegramShareUrl(publicUrl, title);
    case "reddit":
      return buildRedditShareUrl(publicUrl, title);
    case "email":
      return buildEmailShareUrl(publicUrl, title);
    case "pinterest":
      return buildPinterestShareUrl(publicUrl, title);
    default:
      return publicUrl;
  }
}

export async function copyTextToClipboard(text: string): Promise<boolean> {
  if (typeof navigator === "undefined" || !navigator.clipboard) {
    return false;
  }
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}
