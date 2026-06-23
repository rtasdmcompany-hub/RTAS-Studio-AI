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
