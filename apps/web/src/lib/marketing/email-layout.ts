/**
 * Branded HTML email shell — dark-mode friendly, responsive, RTAS identity.
 * Inline styles only (ESP-safe). Used by the marketing template registry.
 */

import { COMPANY_NAME, PRODUCT_NAME } from "@rtas/shared";
import { escapeHtml } from "@/lib/server/html-escape";
import {
  SITE_SUPPORT_EMAIL,
  SITE_HELP_EMAIL,
} from "@/lib/site-links";

const BRAND = {
  bg: "#0b0d12",
  surface: "#141821",
  border: "#2a3140",
  text: "#f4f6fb",
  muted: "#9aa3b5",
  accent: "#c4a574",
  accentText: "#0b0d12",
  link: "#e8d4b0",
} as const;

export type EmailCta = {
  label: string;
  href: string;
};

export type EmailLayoutInput = {
  preheader?: string;
  title: string;
  bodyHtml: string;
  cta?: EmailCta;
  secondaryCta?: EmailCta;
  footerNote?: string;
  unsubscribeUrl?: string;
};

function appBaseUrl(): string {
  return (
    process.env.NEXT_PUBLIC_APP_URL ||
    process.env.NEXTAUTH_URL ||
    "https://rtasstudio.com"
  ).replace(/\/$/, "");
}

export function getMarketingAppUrl(): string {
  return appBaseUrl();
}

export function renderEmailLayout(input: EmailLayoutInput): {
  html: string;
  textFooter: string;
} {
  const base = appBaseUrl();
  const year = new Date().getUTCFullYear();
  const safeTitle = escapeHtml(input.title);
  const safePre = escapeHtml(input.preheader ?? input.title);
  const cta = input.cta
    ? `<p style="margin:28px 0 12px;text-align:center;">
        <a href="${escapeHtml(input.cta.href)}" style="background:${BRAND.accent};color:${BRAND.accentText};text-decoration:none;padding:14px 28px;border-radius:10px;display:inline-block;font-weight:700;font-size:15px;">
          ${escapeHtml(input.cta.label)}
        </a>
      </p>`
    : "";
  const secondary = input.secondaryCta
    ? `<p style="margin:0 0 24px;text-align:center;">
        <a href="${escapeHtml(input.secondaryCta.href)}" style="color:${BRAND.link};font-size:14px;">
          ${escapeHtml(input.secondaryCta.label)}
        </a>
      </p>`
    : "";
  const footerNote = input.footerNote
    ? `<p style="margin:0 0 12px;color:${BRAND.muted};font-size:12px;line-height:1.5;">${escapeHtml(input.footerNote)}</p>`
    : "";
  const unsub = input.unsubscribeUrl
    ? `<p style="margin:8px 0 0;font-size:11px;">
        <a href="${escapeHtml(input.unsubscribeUrl)}" style="color:${BRAND.muted};">Unsubscribe from marketing emails</a>
      </p>`
    : `<p style="margin:8px 0 0;font-size:11px;color:${BRAND.muted};">
        Transactional message — manage preferences in your account.
      </p>`;

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="color-scheme" content="dark light" />
  <meta name="supported-color-schemes" content="dark light" />
  <title>${safeTitle}</title>
  <!--[if mso]><style>body,table,td{font-family:Arial,sans-serif!important;}</style><![endif]-->
</head>
<body style="margin:0;padding:0;background:${BRAND.bg};color:${BRAND.text};">
  <div style="display:none;max-height:0;overflow:hidden;opacity:0;">${safePre}</div>
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:${BRAND.bg};padding:24px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:560px;background:${BRAND.surface};border:1px solid ${BRAND.border};border-radius:16px;overflow:hidden;">
          <tr>
            <td style="padding:28px 28px 8px;border-bottom:1px solid ${BRAND.border};">
              <p style="margin:0;font-family:Georgia,'Times New Roman',serif;font-size:22px;letter-spacing:0.04em;color:${BRAND.accent};">
                ${escapeHtml(PRODUCT_NAME)}
              </p>
              <p style="margin:6px 0 0;font-family:Segoe UI,Arial,sans-serif;font-size:12px;color:${BRAND.muted};">
                ${escapeHtml(COMPANY_NAME)}
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:28px;font-family:Segoe UI,Arial,sans-serif;font-size:15px;line-height:1.65;color:${BRAND.text};">
              <h1 style="margin:0 0 16px;font-size:22px;line-height:1.3;font-weight:700;color:${BRAND.text};">${safeTitle}</h1>
              ${input.bodyHtml}
              ${cta}
              ${secondary}
            </td>
          </tr>
          <tr>
            <td style="padding:20px 28px 28px;border-top:1px solid ${BRAND.border};font-family:Segoe UI,Arial,sans-serif;">
              ${footerNote}
              <p style="margin:0;color:${BRAND.muted};font-size:12px;line-height:1.5;">
                ${escapeHtml(COMPANY_NAME)} ·
                <a href="${escapeHtml(base)}" style="color:${BRAND.link};">${escapeHtml(base.replace(/^https?:\/\//, ""))}</a><br />
                Support: <a href="mailto:${SITE_HELP_EMAIL}" style="color:${BRAND.link};">${SITE_HELP_EMAIL}</a>
                · Sales: <a href="mailto:${SITE_SUPPORT_EMAIL}" style="color:${BRAND.link};">${SITE_SUPPORT_EMAIL}</a>
              </p>
              <p style="margin:12px 0 0;color:${BRAND.muted};font-size:11px;">
                © ${year} ${escapeHtml(COMPANY_NAME)}. All rights reserved.
              </p>
              ${unsub}
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>`.trim();

  const textFooter = [
    "",
    "—",
    `${PRODUCT_NAME} · ${COMPANY_NAME}`,
    base,
    `Support: ${SITE_HELP_EMAIL}`,
    `© ${year} ${COMPANY_NAME}`,
  ].join("\n");

  return { html, textFooter };
}
