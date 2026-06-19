import { COMPANY_NAME, GROUP_NAME, LEGAL_LAST_UPDATED, PRODUCT_NAME } from "./terms";

export const COOKIE_SECTIONS = [
  {
    title: "1. What Are Cookies",
    body: `Cookies and similar technologies (local storage, session storage) help ${PRODUCT_NAME} remember your preferences, keep you signed in, and understand how the site is used.`,
  },
  {
    title: "2. Cookies We Use",
    body: `Essential cookies for authentication and security; preference cookies for studio form backup and UI settings; analytics cookies (if enabled) to improve performance. We do not sell cookie data to advertisers.`,
  },
  {
    title: "3. Third Parties",
    body: `Payment processors (Paddle, Lemon Squeezy) and sign-in providers (e.g. Google) may set their own cookies when you use checkout or OAuth. Their policies apply on their domains.`,
  },
  {
    title: "4. Your Choices",
    body: `You can accept or decline non-essential cookies via our banner. You may also clear cookies in your browser settings. Declining some cookies may limit features such as saved form drafts.`,
  },
  {
    title: "5. Contact",
    body: `Questions: support@rtasdigital.com · ${COMPANY_NAME} · ${GROUP_NAME}. Last updated: ${LEGAL_LAST_UPDATED}.`,
  },
] as const;
