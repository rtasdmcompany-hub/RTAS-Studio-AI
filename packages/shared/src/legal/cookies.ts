import {
  COMPANY_NAME,
  GROUP_NAME,
  LEGAL_ENTITY_STATEMENT,
  LEGAL_LAST_UPDATED,
  PRODUCT_NAME,
} from "./terms";
import type { LegalSection } from "./types";

export const COOKIES_INTRO = `${LEGAL_ENTITY_STATEMENT} This Cookie Policy describes how ${PRODUCT_NAME} uses cookies, local storage, session storage, and similar technologies on our websites and web application. It should be read together with our Privacy Policy and Terms of Service. Where non-essential cookies require consent under ePrivacy, GDPR, or UK PECR rules, we obtain it via our cookie banner before activation.`;

export const COOKIE_SECTIONS: LegalSection[] = [
  {
    title: "1. Scope & Corporate Entity",
    body: `${LEGAL_ENTITY_STATEMENT} Cookies set by ${COMPANY_NAME} on ${PRODUCT_NAME} domains support authentication, security, studio workflow persistence, and — with your consent — analytics. Third parties such as payment processors and OAuth providers may set their own cookies when you interact with their flows.`,
  },
  {
    title: "2. Essential & Functional Cookies",
    body: `Strictly necessary technologies enable core Service functionality and cannot be disabled without breaking sign-in or checkout.`,
    bullets: [
      "Session and authentication tokens (NextAuth / secure HTTP-only cookies).",
      "CSRF and security tokens that protect against cross-site request forgery.",
      "Local storage drafts for studio form fields and UI preferences you explicitly save.",
      "Cookie-consent state so we remember your banner choice.",
    ],
  },
  {
    title: "3. Analytics & Performance Technologies",
    body: `If you accept non-essential cookies, we may use privacy-oriented analytics to measure page performance, feature adoption, and error rates. These tools receive pseudonymous identifiers — not sold to advertisers. Declining analytics cookies does not affect paid features or generation capacity.`,
  },
  {
    title: "4. Third-Party Cookies (Payments, OAuth & CDNs)",
    body: `When you complete checkout or sign in with Google, Merchant-of-Record partners (e.g., Paddle, Lemon Squeezy) and identity providers may set cookies on their domains to prevent fraud, maintain sessions, and comply with PCI-DSS workflows. Content delivery networks may cache assets locally. Their policies govern data on their domains; review each provider's documentation before completing checkout or OAuth.`,
  },
  {
    title: "5. Consent Management & Your Choices",
    body: `Use our cookie banner to accept or decline non-essential categories. You may withdraw consent at any time by clearing site data or revisiting the banner where available. Browser settings allow blocking all cookies; note that blocking essential cookies will prevent login and studio access. For Do-Not-Track signals, we honor applicable legal requirements but may treat DNT as a decline of non-essential analytics where mandated.`,
  },
  {
    title: "6. Retention, Updates & Contact",
    body: `Session cookies expire when you close the browser; persistent cookies and local storage entries typically persist up to twelve (12) months unless cleared earlier. We update this Policy when technologies change. Questions: support@rtasdigital.com · ${COMPANY_NAME} · ${GROUP_NAME}. Last updated: ${LEGAL_LAST_UPDATED}.`,
  },
];
