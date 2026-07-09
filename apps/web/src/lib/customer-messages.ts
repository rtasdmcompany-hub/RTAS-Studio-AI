import type { UserProfile } from "@rtas/shared";

/** Emails that see technical / owner diagnostics in the studio UI. */
const DEFAULT_OWNER_EMAILS: string[] = [];

export function isStudioOwner(profile: UserProfile | null | undefined): boolean {
  if (!profile?.email) return false;
  const extra = process.env.NEXT_PUBLIC_OWNER_EMAILS?.split(",")
    .map((e) => e.trim().toLowerCase())
    .filter(Boolean);
  const owners = new Set(
    [...DEFAULT_OWNER_EMAILS, ...(extra ?? [])].map((e) => e.toLowerCase())
  );
  return owners.has(profile.email.toLowerCase());
}

export const CUSTOMER_STUDIO_BUSY = {
  title: "Studio is busy",
  message:
    "Our AI render farm is at peak demand right now. We are preparing a preview for you — your full video will follow as soon as a slot opens.",
  hint: "You can keep editing your project while we process. No credits have been used for this preview.",
};

export const CUSTOMER_PREVIEW_READY = {
  title: "Preview ready",
  message:
    "Your preview is ready to watch. Full HD export is queued and will be available shortly.",
  hint: "Subscribe or use credits for the final downloadable video when rendering completes.",
};

export const CUSTOMER_CLOUD_MAINTENANCE = {
  title: "Almost there",
  message:
    "We could not finish the full cloud render this second, so we saved a preview for you instead. Please try again in a few minutes for the final export.",
  hint: null,
};

export const CUSTOMER_GENERIC_FAILURE = {
  title: "Could not finish this render",
  message:
    "Something interrupted this video. Your credits were not charged. Please check your inputs and try again.",
  hint: "If this keeps happening, contact RTAS support with your video title.",
};

export const CUSTOMER_CONNECTION_ISSUE = {
  title: "Connection issue",
  message:
    "We lost contact with the render service. Please wait a moment and try again.",
  hint: null,
};

export type CustomerNotice = {
  title: string;
  message: string;
  hint: string | null;
};

export function noticeForOwnerOrCustomer(
  profile: UserProfile | null | undefined,
  owner: CustomerNotice,
  customer: CustomerNotice
): CustomerNotice {
  return isStudioOwner(profile) ? owner : customer;
}

export function isCloudCapacityMessage(message: string): boolean {
  const lower = message.toLowerCase();
  const markers = [
    "fal.ai",
    "fal ",
    "billing",
    "balance",
    "exhausted",
    "owner",
    "paused",
    "wait ",
    "retry",
    "api key",
    "cloud video paused",
    "protect",
    "locked",
    "insufficient",
    "dashboard/billing",
    "render farm",
    "peak demand",
  ];
  return markers.some((m) => lower.includes(m));
}

/** Internal diagnostics — never show in the customer preview banner. */
export function isOwnerDiagnosticMessage(message: string, title = ""): boolean {
  return isCloudCapacityMessage(`${title} ${message}`);
}
