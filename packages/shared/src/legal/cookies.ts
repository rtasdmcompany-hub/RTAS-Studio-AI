import {
  COMPANY_NAME,
  LEGAL_CONTACT_EMAIL,
  LEGAL_ENTITY_STATEMENT,
  LEGAL_LOCATION_STATEMENT,
  LEGAL_SUPPORT_EMAIL,
  PRODUCT_NAME,
} from "./terms";
import type { LegalSection } from "./types";

export const COOKIES_INTRO = `${LEGAL_ENTITY_STATEMENT} This Cookie Policy describes how ${PRODUCT_NAME} uses cookies, local storage, session storage, and similar technologies on our websites and web application. It should be read together with our Privacy Policy and Terms of Service. Where non-essential cookies require consent under ePrivacy, GDPR, or UK PECR rules, we obtain it via our cookie banner before activating optional Analytics or Marketing technologies.`;

export const COOKIE_SECTIONS: LegalSection[] = [
  {
    title: "1. Scope & Operator",
    body: `${LEGAL_ENTITY_STATEMENT} Cookies set by ${COMPANY_NAME} on ${PRODUCT_NAME} domains support authentication, security, studio workflow persistence, and — with your consent — analytics or marketing measurement. Third parties such as our Merchant of Record (Paddle) and OAuth providers may set their own cookies when you interact with their flows.`,
  },
  {
    title: "2. Cookie Categories",
    body: `We group technologies into three categories. Necessary cookies always run. Analytics and Marketing run only after you opt in via the banner or preference center.`,
    bullets: [
      "Necessary — sign-in, security, CSRF protection, consent storage, and core studio preferences required for the Service to function.",
      "Analytics — optional product and performance measurement (pseudonymous). Disabled until you enable Analytics or Accept all.",
      "Marketing — optional campaign or advertising measurement pixels when configured. Disabled until you enable Marketing or Accept all. Not used to sell personal data.",
    ],
  },
  {
    title: "3. Necessary & Functional Cookies",
    body: `Strictly necessary technologies enable core Service functionality and cannot be disabled without breaking sign-in or checkout.`,
    bullets: [
      "Session and authentication tokens (secure HTTP-only cookies).",
      "CSRF and security tokens that protect against cross-site request forgery.",
      "Local storage for studio form fields and UI preferences you explicitly save.",
      "Cookie-consent preference state so we remember Necessary / Analytics / Marketing choices.",
    ],
  },
  {
    title: "4. Analytics & Performance Technologies",
    body: `If you enable Analytics, we may use privacy-oriented measurement to understand page performance, feature adoption, and error rates. These tools receive pseudonymous identifiers — not sold to advertisers. Declining Analytics does not affect paid features, Credits, or generation capacity. Optional vendor scripts are not loaded until consent is granted.`,
  },
  {
    title: "5. Marketing Technologies",
    body: `If you enable Marketing, we may load campaign or advertising measurement tags when those vendors are configured by operations. You can withdraw Marketing consent at any time without losing access to Studio. Checkout and OAuth cookies set by Paddle or Google on their domains remain governed by those providers.`,
  },
  {
    title: "6. Third-Party Cookies (Payments, OAuth & CDNs)",
    body: `When you complete checkout or sign in with Google, our Merchant of Record (Paddle) and identity providers may set cookies on their domains to prevent fraud, maintain sessions, and comply with PCI-DSS workflows. Content delivery networks may cache assets locally. Their policies govern data on their domains; review each provider's documentation before completing checkout or OAuth.`,
  },
  {
    title: "7. Consent Management & Withdrawal",
    body: `Use the cookie banner to Accept all, keep Necessary only, or Manage preferences (Necessary / Analytics / Marketing). Reopen preferences anytime via Cookie settings on this page, the footer link where available, or Privacy settings in your dashboard (/profile/privacy). Withdraw consent by switching categories off; optional trackers stop for new loads. Browser settings allow blocking all cookies; blocking Necessary cookies will prevent login and studio access.`,
  },
  {
    title: "8. Retention, Updates & Contact",
    body: `Session cookies expire when you close the browser; persistent cookies and local storage entries typically persist up to twelve (12) months unless cleared earlier. We update this Policy when technologies change. Questions: ${LEGAL_SUPPORT_EMAIL} · ${LEGAL_CONTACT_EMAIL} · ${COMPANY_NAME} · ${LEGAL_LOCATION_STATEMENT}.`,
  },
];

