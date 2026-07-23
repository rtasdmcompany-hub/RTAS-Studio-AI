/**
 * Email template registry — Phase 13 Sprint 4.
 * Integrity: templates + hooks only. No fabricated open/click rates.
 */

import {
  PRODUCT_NAME,
  TESTER_CREDITS,
  TESTER_DURATION_DAYS,
  TESTER_PRICE_USD,
  STANDARD_PRICE_USD,
  PREMIUM_PRICE_USD,
} from "@rtas/shared";
import { escapeHtml } from "@/lib/server/html-escape";
import {
  getMarketingAppUrl,
  renderEmailLayout,
} from "@/lib/marketing/email-layout";

export type EmailTemplateId =
  | "welcome"
  | "verification"
  | "password_reset"
  | "weekly_updates"
  | "feature_announcements"
  | "release_notes"
  | "newsletter"
  | "billing_notifications"
  | "subscription_expiry"
  | "payment_success"
  | "payment_failure"
  | "enterprise_followup"
  | "video_ready";

export type TemplateHookStatus = "live" | "planned";

export type EmailTemplateMeta = {
  id: EmailTemplateId;
  name: string;
  category: "auth" | "product" | "billing" | "marketing" | "sales";
  description: string;
  /** live = send hook exists on a real event; planned = campaign not scheduled yet */
  hookStatus: TemplateHookStatus;
  trigger: string;
};

export const EMAIL_TEMPLATE_REGISTRY: EmailTemplateMeta[] = [
  {
    id: "welcome",
    name: "Welcome",
    category: "auth",
    description: "Orient new users after email verification.",
    hookStatus: "live",
    trigger: "Email verified",
  },
  {
    id: "verification",
    name: "Verification",
    category: "auth",
    description: "Confirm credentials signup email.",
    hookStatus: "live",
    trigger: "Register / resend verification",
  },
  {
    id: "password_reset",
    name: "Password Reset",
    category: "auth",
    description: "One-hour reset link for credentials accounts.",
    hookStatus: "live",
    trigger: "Forgot password",
  },
  {
    id: "weekly_updates",
    name: "Weekly Updates",
    category: "marketing",
    description: "Product tips and studio highlights for opted-in subscribers.",
    hookStatus: "planned",
    trigger: "Planned — cron + newsletter list (not scheduled)",
  },
  {
    id: "feature_announcements",
    name: "Feature Announcements",
    category: "product",
    description: "Ship meaningful product changes to opted-in users.",
    hookStatus: "planned",
    trigger: "Planned — ops campaign send",
  },
  {
    id: "release_notes",
    name: "Release Notes",
    category: "product",
    description: "Version changelog digest.",
    hookStatus: "planned",
    trigger: "Planned — release publish",
  },
  {
    id: "newsletter",
    name: "Newsletter",
    category: "marketing",
    description: "General marketing newsletter for subscribers.",
    hookStatus: "planned",
    trigger: "Planned — marketing calendar",
  },
  {
    id: "billing_notifications",
    name: "Billing Notifications",
    category: "billing",
    description: "Plan / credit ledger notices.",
    hookStatus: "live",
    trigger: "Subscription activated / renewed / cancelled webhook",
  },
  {
    id: "subscription_expiry",
    name: "Subscription Expiry",
    category: "billing",
    description: "Credits or period nearing end.",
    hookStatus: "live",
    trigger: "Credits expire within window / cancel-at-period-end",
  },
  {
    id: "payment_success",
    name: "Payment Success",
    category: "billing",
    description: "Confirm successful checkout or renewal.",
    hookStatus: "live",
    trigger: "subscription_activated / subscription_renewed",
  },
  {
    id: "payment_failure",
    name: "Payment Failure",
    category: "billing",
    description: "Payment failed — retry or update method.",
    hookStatus: "planned",
    trigger: "Planned — provider payment_failed webhook (when emitted)",
  },
  {
    id: "enterprise_followup",
    name: "Enterprise Follow-up",
    category: "sales",
    description: "Auto-ack to enterprise / beta / partner lead submitters.",
    hookStatus: "live",
    trigger: "Commercial lead form submitted",
  },
  {
    id: "video_ready",
    name: "Video Ready",
    category: "product",
    description: "Render complete notification.",
    hookStatus: "live",
    trigger: "POST /api/notify/video-ready",
  },
];

export type RenderedEmail = {
  templateId: EmailTemplateId;
  subject: string;
  html: string;
  text: string;
};

function p(html: string): string {
  return `<p style="margin:0 0 14px;">${html}</p>`;
}

export function renderVerificationEmail(input: {
  name: string;
  verifyUrl: string;
}): RenderedEmail {
  const name = escapeHtml(input.name || "there");
  const body = [
    p(`Hi ${name},`),
    p(
      `Thanks for signing up for ${escapeHtml(PRODUCT_NAME)}. Confirm your email to activate your account.`
    ),
    p(
      `<span style="color:#9aa3b5;font-size:13px;">This link expires in 24 hours. If you did not create an account, ignore this email.</span>`
    ),
  ].join("");
  const { html, textFooter } = renderEmailLayout({
    title: "Confirm your email",
    preheader: `Confirm your ${PRODUCT_NAME} account`,
    bodyHtml: body,
    cta: { label: "Confirm my account", href: input.verifyUrl },
  });
  const text = [
    `Hi ${input.name || "there"},`,
    "",
    `Confirm your ${PRODUCT_NAME} account:`,
    input.verifyUrl,
    "",
    "This link expires in 24 hours.",
    textFooter,
  ].join("\n");
  return {
    templateId: "verification",
    subject: `Confirm your ${PRODUCT_NAME} account`,
    html,
    text,
  };
}

export function renderWelcomeEmail(input: { name: string }): RenderedEmail {
  const base = getMarketingAppUrl();
  const name = escapeHtml(input.name || "there");
  const body = [
    p(`Hi ${name},`),
    p(
      `Welcome to ${escapeHtml(PRODUCT_NAME)} — cinematic AI video with Authorized Identity Preservation, priced by the second (1 credit = 1 second).`
    ),
    p(
      `Start with <strong>Tester</strong> ($${TESTER_PRICE_USD} · ${TESTER_CREDITS}s · ${TESTER_DURATION_DAYS} days), then scale to Standard ($${STANDARD_PRICE_USD}/mo) or Premium 4K ($${PREMIUM_PRICE_USD}/mo).`
    ),
    p(`Open Studio to compose your first render, or review pricing first.`),
  ].join("");
  const { html, textFooter } = renderEmailLayout({
    title: `Welcome to ${PRODUCT_NAME}`,
    preheader: "Your studio is ready — start with Tester or open Studio",
    bodyHtml: body,
    cta: { label: "Open Studio", href: `${base}/studio` },
    secondaryCta: { label: "View pricing", href: `${base}/pricing` },
    footerNote: "You received this because you verified your account.",
  });
  const text = [
    `Hi ${input.name || "there"},`,
    "",
    `Welcome to ${PRODUCT_NAME}.`,
    `Tester: $${TESTER_PRICE_USD} / ${TESTER_CREDITS}s / ${TESTER_DURATION_DAYS} days.`,
    `Studio: ${base}/studio`,
    `Pricing: ${base}/pricing`,
    textFooter,
  ].join("\n");
  return {
    templateId: "welcome",
    subject: `Welcome to ${PRODUCT_NAME}`,
    html,
    text,
  };
}

export function renderPasswordResetEmail(input: {
  name: string;
  resetUrl: string;
}): RenderedEmail {
  const name = escapeHtml(input.name || "there");
  const body = [
    p(`Hi ${name},`),
    p(
      `We received a request to reset the password for your ${escapeHtml(PRODUCT_NAME)} account.`
    ),
    p(
      `<span style="color:#9aa3b5;font-size:13px;">This link expires in 1 hour. If you did not request a reset, you can ignore this email.</span>`
    ),
  ].join("");
  const { html, textFooter } = renderEmailLayout({
    title: "Reset your password",
    bodyHtml: body,
    cta: { label: "Reset password", href: input.resetUrl },
  });
  const text = [
    `Hi ${input.name || "there"},`,
    "",
    `Reset your ${PRODUCT_NAME} password:`,
    input.resetUrl,
    "",
    "This link expires in 1 hour.",
    textFooter,
  ].join("\n");
  return {
    templateId: "password_reset",
    subject: `Reset your ${PRODUCT_NAME} password`,
    html,
    text,
  };
}

export function renderVideoReadyEmail(input: {
  name?: string;
  title: string;
  durationLabel: string;
  watchUrl: string;
}): RenderedEmail {
  const name = escapeHtml(input.name || "");
  const body = [
    p(`Hi${name ? ` ${name}` : ""},`),
    p(
      `Your video <strong>${escapeHtml(input.title)}</strong> (${escapeHtml(input.durationLabel)}) is ready.`
    ),
  ].join("");
  const { html, textFooter } = renderEmailLayout({
    title: "Your video is ready",
    bodyHtml: body,
    cta: { label: "Watch your video", href: input.watchUrl },
  });
  const text = [
    `Hi${input.name ? ` ${input.name}` : ""},`,
    "",
    `Your video "${input.title}" (${input.durationLabel}) is ready.`,
    input.watchUrl,
    textFooter,
  ].join("\n");
  return {
    templateId: "video_ready",
    subject: `${PRODUCT_NAME} — your video is ready`,
    html,
    text,
  };
}

export function renderPaymentSuccessEmail(input: {
  name?: string;
  planLabel: string;
  credits?: number;
}): RenderedEmail {
  const base = getMarketingAppUrl();
  const name = escapeHtml(input.name || "there");
  const creditsLine =
    typeof input.credits === "number"
      ? p(`Credits on your account: <strong>${input.credits}</strong> seconds.`)
      : "";
  const body = [
    p(`Hi ${name},`),
    p(
      `Payment confirmed for <strong>${escapeHtml(input.planLabel)}</strong> on ${escapeHtml(PRODUCT_NAME)}.`
    ),
    creditsLine,
    p(`Open Studio to start rendering, or review billing on your Dashboard.`),
  ].join("");
  const { html, textFooter } = renderEmailLayout({
    title: "Payment successful",
    bodyHtml: body,
    cta: { label: "Open Studio", href: `${base}/studio` },
    secondaryCta: { label: "Dashboard", href: `${base}/profile` },
  });
  const text = [
    `Hi ${input.name || "there"},`,
    "",
    `Payment confirmed for ${input.planLabel}.`,
    typeof input.credits === "number" ? `Credits: ${input.credits}s` : "",
    `${base}/studio`,
    textFooter,
  ]
    .filter(Boolean)
    .join("\n");
  return {
    templateId: "payment_success",
    subject: `${PRODUCT_NAME} — payment successful`,
    html,
    text,
  };
}

export function renderPaymentFailureEmail(input: {
  name?: string;
  planLabel?: string;
}): RenderedEmail {
  const base = getMarketingAppUrl();
  const name = escapeHtml(input.name || "there");
  const body = [
    p(`Hi ${name},`),
    p(
      `We could not process a payment${input.planLabel ? ` for <strong>${escapeHtml(input.planLabel)}</strong>` : ""} on ${escapeHtml(PRODUCT_NAME)}.`
    ),
    p(`Update your payment method with the checkout provider, or contact support if this looks wrong.`),
  ].join("");
  const { html, textFooter } = renderEmailLayout({
    title: "Payment failed",
    bodyHtml: body,
    cta: { label: "View pricing", href: `${base}/pricing` },
    secondaryCta: { label: "Contact support", href: `${base}/help/contact` },
  });
  const text = [
    `Hi ${input.name || "there"},`,
    "",
    "Payment failed.",
    `${base}/pricing`,
    textFooter,
  ].join("\n");
  return {
    templateId: "payment_failure",
    subject: `${PRODUCT_NAME} — payment failed`,
    html,
    text,
  };
}

export function renderSubscriptionExpiryEmail(input: {
  name?: string;
  expireLabel: string;
}): RenderedEmail {
  const base = getMarketingAppUrl();
  const name = escapeHtml(input.name || "there");
  const body = [
    p(`Hi ${name},`),
    p(
      `Your ${escapeHtml(PRODUCT_NAME)} credits or subscription period is set to end on <strong>${escapeHtml(input.expireLabel)}</strong>.`
    ),
    p(`Renew or upgrade to keep rendering without interruption.`),
  ].join("");
  const { html, textFooter } = renderEmailLayout({
    title: "Subscription / credits expiring",
    bodyHtml: body,
    cta: { label: "Manage plans", href: `${base}/pricing` },
  });
  const text = [
    `Hi ${input.name || "there"},`,
    "",
    `Credits/subscription ending: ${input.expireLabel}`,
    `${base}/pricing`,
    textFooter,
  ].join("\n");
  return {
    templateId: "subscription_expiry",
    subject: `${PRODUCT_NAME} — credits or plan expiring`,
    html,
    text,
  };
}

export function renderBillingNotificationEmail(input: {
  name?: string;
  headline: string;
  detail: string;
}): RenderedEmail {
  const base = getMarketingAppUrl();
  const name = escapeHtml(input.name || "there");
  const body = [
    p(`Hi ${name},`),
    p(escapeHtml(input.detail)),
  ].join("");
  const { html, textFooter } = renderEmailLayout({
    title: input.headline,
    bodyHtml: body,
    cta: { label: "Open Dashboard", href: `${base}/profile` },
  });
  const text = [
    `Hi ${input.name || "there"},`,
    "",
    input.headline,
    input.detail,
    `${base}/profile`,
    textFooter,
  ].join("\n");
  return {
    templateId: "billing_notifications",
    subject: `${PRODUCT_NAME} — ${input.headline}`,
    html,
    text,
  };
}

export function renderEnterpriseFollowupEmail(input: {
  name: string;
  kindLabel: string;
}): RenderedEmail {
  const base = getMarketingAppUrl();
  const name = escapeHtml(input.name);
  const body = [
    p(`Hi ${name},`),
    p(
      `Thanks for your <strong>${escapeHtml(input.kindLabel)}</strong> submission to ${escapeHtml(PRODUCT_NAME)}. Our team will review and follow up by email.`
    ),
    p(
      `Meanwhile, explore the product docs, pricing (Tester $${TESTER_PRICE_USD} · Standard $${STANDARD_PRICE_USD} · Premium $${PREMIUM_PRICE_USD}), and Customer Success center.`
    ),
  ].join("");
  const { html, textFooter } = renderEmailLayout({
    title: "We received your request",
    bodyHtml: body,
    cta: { label: "Customer Success", href: `${base}/help` },
    secondaryCta: { label: "View pricing", href: `${base}/pricing` },
  });
  const text = [
    `Hi ${input.name},`,
    "",
    `Thanks for your ${input.kindLabel} submission.`,
    `We will follow up by email.`,
    `${base}/help`,
    textFooter,
  ].join("\n");
  return {
    templateId: "enterprise_followup",
    subject: `${PRODUCT_NAME} — we received your request`,
    html,
    text,
  };
}

/** Planned campaign templates — renderable for preview; not auto-sent. */
export function renderPlannedCampaignEmail(input: {
  templateId: Extract<
    EmailTemplateId,
    "weekly_updates" | "feature_announcements" | "release_notes" | "newsletter"
  >;
  name?: string;
  headline: string;
  body: string;
  ctaLabel: string;
  ctaHref: string;
}): RenderedEmail {
  const name = escapeHtml(input.name || "there");
  const unsub = `${getMarketingAppUrl()}/profile/notifications`;
  const bodyHtml = [
    p(`Hi ${name},`),
    p(escapeHtml(input.body)),
  ].join("");
  const titles: Record<typeof input.templateId, string> = {
    weekly_updates: "Weekly Studio update",
    feature_announcements: "New feature",
    release_notes: "Release notes",
    newsletter: "Newsletter",
  };
  const { html, textFooter } = renderEmailLayout({
    title: input.headline || titles[input.templateId],
    bodyHtml,
    cta: { label: input.ctaLabel, href: input.ctaHref },
    unsubscribeUrl: unsub,
    footerNote: "Planned campaign template — sent only to opted-in subscribers when scheduled.",
  });
  const text = [
    `Hi ${input.name || "there"},`,
    "",
    input.headline,
    input.body,
    input.ctaHref,
    textFooter,
  ].join("\n");
  return {
    templateId: input.templateId,
    subject: `${PRODUCT_NAME} — ${input.headline}`,
    html,
    text,
  };
}

export function getTemplateMeta(id: EmailTemplateId): EmailTemplateMeta | undefined {
  return EMAIL_TEMPLATE_REGISTRY.find((t) => t.id === id);
}
