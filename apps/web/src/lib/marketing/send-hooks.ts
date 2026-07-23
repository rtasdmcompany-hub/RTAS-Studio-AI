/**
 * Transactional send helpers that use the template registry + respect prefs.
 */

import { sendEmail } from "@/lib/server/mailer";
import {
  renderBillingNotificationEmail,
  renderEnterpriseFollowupEmail,
  renderPaymentSuccessEmail,
  renderSubscriptionExpiryEmail,
  renderWelcomeEmail,
  type EmailTemplateId,
} from "@/lib/marketing/email-templates";
import { getNotificationPrefs } from "@/lib/marketing/notifications";
import { isPrismaConfigured, prisma } from "@/lib/prisma";

async function logSend(input: {
  templateId: EmailTemplateId;
  toEmail: string;
  userId?: string;
  subject: string;
  ok: boolean;
  provider?: string;
  error?: string;
}) {
  if (!isPrismaConfigured()) return;
  try {
    await prisma.emailSendLog.create({
      data: {
        templateId: input.templateId,
        toEmail: input.toEmail,
        userId: input.userId,
        subject: input.subject,
        status: input.ok ? "sent" : "failed",
        provider: input.provider ?? null,
        error: input.error?.slice(0, 500) ?? null,
      },
    });
  } catch {
    /* non-blocking */
  }
}

export async function sendWelcomeEmail(input: {
  userId?: string;
  email: string;
  name: string;
}) {
  const rendered = renderWelcomeEmail({ name: input.name });
  const result = await sendEmail({
    to: input.email,
    subject: rendered.subject,
    html: rendered.html,
    text: rendered.text,
  });
  await logSend({
    templateId: "welcome",
    toEmail: input.email,
    userId: input.userId,
    subject: rendered.subject,
    ok: result.ok,
    provider: result.provider,
    error: result.error,
  });
  return result;
}

export async function sendPaymentSuccessEmail(input: {
  userId?: string;
  email: string;
  name?: string;
  planLabel: string;
  credits?: number;
}) {
  if (input.userId) {
    const prefs = await getNotificationPrefs(input.userId);
    if (!prefs.emailBilling) {
      return { ok: true, provider: "link-only" as const, skipped: true };
    }
  }
  const rendered = renderPaymentSuccessEmail({
    name: input.name,
    planLabel: input.planLabel,
    credits: input.credits,
  });
  const result = await sendEmail({
    to: input.email,
    subject: rendered.subject,
    html: rendered.html,
    text: rendered.text,
  });
  await logSend({
    templateId: "payment_success",
    toEmail: input.email,
    userId: input.userId,
    subject: rendered.subject,
    ok: result.ok,
    provider: result.provider,
    error: result.error,
  });
  return result;
}

export async function sendBillingNotificationEmail(input: {
  userId?: string;
  email: string;
  name?: string;
  headline: string;
  detail: string;
}) {
  if (input.userId) {
    const prefs = await getNotificationPrefs(input.userId);
    if (!prefs.emailBilling) {
      return { ok: true, provider: "link-only" as const, skipped: true };
    }
  }
  const rendered = renderBillingNotificationEmail({
    name: input.name,
    headline: input.headline,
    detail: input.detail,
  });
  const result = await sendEmail({
    to: input.email,
    subject: rendered.subject,
    html: rendered.html,
    text: rendered.text,
  });
  await logSend({
    templateId: "billing_notifications",
    toEmail: input.email,
    userId: input.userId,
    subject: rendered.subject,
    ok: result.ok,
    provider: result.provider,
    error: result.error,
  });
  return result;
}

export async function sendSubscriptionExpiryEmail(input: {
  userId?: string;
  email: string;
  name?: string;
  expireLabel: string;
}) {
  if (input.userId) {
    const prefs = await getNotificationPrefs(input.userId);
    if (!prefs.emailBilling) {
      return { ok: true, provider: "link-only" as const, skipped: true };
    }
  }
  const rendered = renderSubscriptionExpiryEmail({
    name: input.name,
    expireLabel: input.expireLabel,
  });
  const result = await sendEmail({
    to: input.email,
    subject: rendered.subject,
    html: rendered.html,
    text: rendered.text,
  });
  await logSend({
    templateId: "subscription_expiry",
    toEmail: input.email,
    userId: input.userId,
    subject: rendered.subject,
    ok: result.ok,
    provider: result.provider,
    error: result.error,
  });
  return result;
}

export async function sendEnterpriseFollowupEmail(input: {
  email: string;
  name: string;
  kindLabel: string;
}) {
  const rendered = renderEnterpriseFollowupEmail({
    name: input.name,
    kindLabel: input.kindLabel,
  });
  const result = await sendEmail({
    to: input.email,
    subject: rendered.subject,
    html: rendered.html,
    text: rendered.text,
  });
  await logSend({
    templateId: "enterprise_followup",
    toEmail: input.email,
    subject: rendered.subject,
    ok: result.ok,
    provider: result.provider,
    error: result.error,
  });
  return result;
}
