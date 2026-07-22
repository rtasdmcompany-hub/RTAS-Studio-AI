import {
  PREMIUM_CREDITS,
  PREMIUM_PRICE_USD,
  STANDARD_CREDITS,
  STANDARD_PRICE_USD,
  TESTER_CREDITS,
  TESTER_DURATION_DAYS,
  TESTER_PRICE_USD,
} from "../credits";
import type { LegalDocumentMeta, LegalSection } from "./types";

/** Operating company (not a payment Merchant of Record). */
export const COMPANY_NAME = "RTAS Digital Marketing Company";

/**
 * Brand ecosystem label only — not a registered legal entity.
 * Prefer {@link LEGAL_ENTITY_STATEMENT} in policy prose.
 */
export const GROUP_NAME = "RTAS brand ecosystem";

export const PRODUCT_NAME = "RTAS Studio AI";

export const LEGAL_JURISDICTION = "Pakistan";

/** Consistent location phrasing across all legal documents. */
export const LEGAL_LOCATION_STATEMENT = `Operating from ${LEGAL_JURISDICTION}`;

/**
 * Canonical entity / operator statement — no ambiguity about registration
 * of a “group of companies.”
 */
export const LEGAL_ENTITY_STATEMENT = `${PRODUCT_NAME} is developed and operated by ${COMPANY_NAME}. Part of the ${GROUP_NAME}. ${COMPANY_NAME} operates from ${LEGAL_JURISDICTION}.`;

/** Document versioning — displayed on every legal page. */
export const LEGAL_DOCUMENT_VERSION = "1.1";
export const LEGAL_EFFECTIVE_DATE = "22 July 2026";
export const LEGAL_LAST_UPDATED = "22 July 2026";

export const LEGAL_META: LegalDocumentMeta = {
  version: LEGAL_DOCUMENT_VERSION,
  effectiveDate: LEGAL_EFFECTIVE_DATE,
  lastUpdated: LEGAL_LAST_UPDATED,
};

/** Public contact addresses (designated for Forward Email / support routing). */
export const LEGAL_SUPPORT_EMAIL = "support@rtasstudio.com";
export const LEGAL_CONTACT_EMAIL = "contact@rtasstudio.com";
export const LEGAL_LEGAL_EMAIL = "legal@rtasstudio.com";
export const LEGAL_PRIVACY_EMAIL = "privacy@rtasstudio.com";

export const TERMS_INTRO = `${LEGAL_ENTITY_STATEMENT} These Terms of Service ("Terms") govern your access to and use of the ${PRODUCT_NAME} platform, including web applications, APIs, generated media, and related support services (collectively, the "Service"). By creating an account, purchasing credits or a subscription, or otherwise using the Service, you enter a binding agreement with ${COMPANY_NAME}. If you do not agree, you must discontinue use immediately.`;

export const TERMS_SECTIONS: LegalSection[] = [
  {
    title: "1. Operator & Proprietary Software",
    body: `${LEGAL_ENTITY_STATEMENT} All intellectual property in the Service — including source code, model orchestration, user interfaces, workflows, branding, documentation, and derivative tooling — is owned exclusively by ${COMPANY_NAME}. Except for the limited licenses expressly granted in these Terms, no title or ownership interest is transferred to you. Reverse engineering, redistribution, or creation of competing services from the Service is prohibited unless permitted by mandatory law.`,
  },
  {
    title: "2. Agreement to Terms & Eligibility",
    body: `By accessing the Service you confirm that you are at least the age of digital consent in your jurisdiction (typically 16–18, or 13 with verifiable parental consent where applicable), that you have authority to bind any organization on whose behalf you register, and that you agree to these Terms, our Privacy Policy, Cookie Policy, Refund Policy, AI Usage Policy, and Trust & Safety rules. Enterprise or agency accounts must ensure end-user compliance.`,
  },
  {
    title: "3. Service Description & AI Processing",
    body: `${PRODUCT_NAME} provides AI-assisted video generation from text, lyrics, images, voice, and related inputs, including Authorized Identity Preservation ("Identity Consistency") workflows for user-owned or authorized likenesses only. The Service is marketed for text-to-video, image-to-video, marketing videos, commercials, social content, music videos, animation, original AI characters, talking avatars with lip sync on authorized media, and related editing tools. Output quality, latency, and availability depend on your subscription tier, fair-use limits, GPU availability and load, and third-party model providers. We may modify features, models, or capacity with reasonable notice where practicable.`,
  },
  {
    title: "4. Plans, Credits & Billing",
    body: `Paid plans grant generation Credits. One (1) Credit equals one (1) second of rendered video unless otherwise stated at checkout. Credits represent computational AI resources allocated to your account; they do not constitute ownership of media, storage entitlements beyond Service rules, or a cash balance. Prices are listed in United States Dollars unless your checkout session displays local currency via our Merchant of Record. Applicable sales tax, VAT, or GST is calculated and collected by Paddle at checkout.`,
    bullets: [
      `Tester: USD ${TESTER_PRICE_USD} one-time evaluation access · ${TESTER_CREDITS} Credits (${TESTER_CREDITS} seconds) · ${TESTER_DURATION_DAYS}-day access window · evaluation-tier output (including watermarked exports where applicable).`,
      `Standard: USD ${STANDARD_PRICE_USD}/month · ${STANDARD_CREDITS} Credits per billing period · 1080p HD masters, clean exports, and commercial download licensing.`,
      `Premium: USD ${PREMIUM_PRICE_USD}/month · ${PREMIUM_CREDITS} Credits per billing period · 4K cinematic masters with priority Identity Preservation queuing.`,
      "Monthly Credits on Standard and Premium reset at the end of each billing period; early renewal may roll unused Credits forward per in-app rules.",
      "Plan upgrades or downgrades may take effect immediately and may adjust billing and Credit allotments according to checkout and account rules.",
    ],
  },
  {
    title: "5. Payment, Merchant of Record (Paddle) & Refunds",
    body: `Card, wallet, and local payment methods are processed by our Merchant of Record ("MoR"), Paddle, which is the legal seller of paid ${PRODUCT_NAME} purchases to you. Paddle calculates applicable sales tax, VAT, or GST, issues compliant invoices/receipts, screens for fraud, and handles buyer refunds and chargebacks under Paddle's Buyer Terms and Refund Policy. ${COMPANY_NAME} does not store full payment card numbers on its servers and does not pay card refunds directly. Settlement to ${COMPANY_NAME} follows Paddle's payout schedule. Except where mandatory consumer-protection law requires otherwise, Transactions are generally non-refundable after delivery or Credit use. For refunds, cancellations, and receipt lookups, use your Paddle confirmation email or https://paddle.net. Contact Paddle (and, for product issues, ${LEGAL_SUPPORT_EMAIL} or ${LEGAL_CONTACT_EMAIL}) before filing a chargeback. See our Refund Policy at https://rtasstudio.com/refund and Paddle's Refund Policy at https://www.paddle.com/legal/refund-policy.`,
  },
  {
    title: "6. Commercial Licensing & Download Rights",
    body: `Active paid subscribers on Standard or Premium receive a worldwide, non-exclusive license to commercially exploit AI-generated outputs they lawfully create through the Service, including public performance, advertising, and client delivery, provided: (a) you comply with these Terms; (b) you own or hold valid licenses for all inputs (likeness, voice, music, trademarks, and other rights); and (c) you respect third-party AI provider acceptable-use policies. Tester and non-subscribed preview outputs remain for private evaluation only unless upgraded. ${COMPANY_NAME} grants no rights beyond this scope.`,
  },
  {
    title: "7. Free Previews, Watermarks & Evaluation Content",
    body: `Watermarked or preview-tier exports are licensed solely for private review within the Service. You may not remove, obscure, or circumvent watermarks, commercially distribute preview content, broadcast it, or monetize screen recordings containing evaluation marks. Upgrading to a paid plan with clean-export entitlements is required before public or commercial release.`,
  },
  {
    title: "8. User Content, Representations & IP Indemnity",
    body: `You retain ownership of lawful uploads. You grant ${COMPANY_NAME} a limited, worldwide license to host, process, transmit, and transform uploads solely to operate, secure, and improve the Service. You represent that your inputs and published outputs do not infringe third-party rights, violate publicity or privacy laws, or breach platform policies. You agree to indemnify ${COMPANY_NAME} against claims arising from your content or misuse, to the extent permitted by law.`,
  },
  {
    title: "9. AI Output Disclaimer & Identity Preservation Limitations",
    body: `Generative AI may produce inaccurate, offensive, or unintended resemblance to third-party works or persons. Authorized Identity Preservation / User Identity Consistency tooling improves consistency across scenes for likenesses you own or are authorized to use; it does not constitute face swapping, celebrity cloning, or a deepfake product, and it does not guarantee perfect likeness or legal clearance for commercial likeness use. You are solely responsible for reviewing, clearing, and approving all outputs before publication or monetization. Artistic preference, stylistic taste, or subjective dissatisfaction with AI output is not, by itself, a technical defect. See also our Trust & Safety page (/trust-safety) and AI Usage Policy (/ai-policy).`,
  },
  {
    title: "10. Prohibited Uses & Acceptable Use",
    body: `You may not use the Service for illegal activity, harassment, hate speech, exploitation of minors, malware distribution, sanctions evasion, or infringement of intellectual property or personality rights. In particular, the following are strictly prohibited. We may suspend or terminate accounts, preserve evidence, and cooperate with law enforcement, regulators, or our Merchant of Record where required. Violations of these Terms are not eligible for refunds.`,
    bullets: [
      "Face swapping, face replacement, or any workflow that maps one person's face onto another.",
      "Celebrity cloning, celebrity generators, or impersonation of public figures.",
      "Identity theft, identity fraud, or deceptive synthetic media of real people without authorization.",
      "Deepfake generation intended to mislead, defraud, harass, or harm.",
      "Voice cloning of real people without their permission.",
      "Fraud, scams, political manipulation, or illegal content.",
      "Sexual content involving minors or non-consenting individuals.",
      "Automated scraping or API abuse beyond documented rate limits.",
    ],
  },
  {
    title: "11. Privacy, Data Processing & Cross-Border Transfers",
    body: `Personal data is processed as described in our Privacy Policy. By using the Service you acknowledge that data may be transferred to the United States, European Union, United Kingdom, Pakistan, and other regions where we or subprocessors operate, subject to appropriate safeguards where required by GDPR, UK GDPR, or comparable frameworks.`,
  },
  {
    title: "12. Governing Law & Dispute Resolution",
    body: `These Terms are governed by the laws of ${LEGAL_JURISDICTION}, without regard to conflict-of-law rules, except where mandatory consumer protections in your country of residence require otherwise. Nothing in these Terms limits non-waivable rights under EU, UK, Australian, Canadian, or other consumer-protection statutes. Disputes should first be addressed to ${LEGAL_CONTACT_EMAIL} or ${LEGAL_LEGAL_EMAIL}; where arbitration or courts are permitted, you agree to individual resolution and waive class actions to the extent enforceable.`,
  },
  {
    title: "13. Limitation of Liability & Warranty Disclaimer",
    body: `THE SERVICE IS PROVIDED "AS IS" AND "AS AVAILABLE." TO THE MAXIMUM EXTENT PERMITTED BY LAW, ${COMPANY_NAME} DISCLAIMS IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT. NEITHER ${COMPANY_NAME} NOR ITS SUPPLIERS SHALL BE LIABLE FOR INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, OR LOST PROFITS. AGGREGATE LIABILITY SHALL NOT EXCEED THE FEES YOU PAID FOR THE SERVICE IN THE TWELVE (12) MONTHS PRECEDING THE CLAIM (THROUGH OUR MERCHANT OF RECORD OR OTHERWISE). Generation speed and availability depend on GPU capacity and third-party infrastructure; temporary slowdowns or outages do not, by themselves, create liability beyond these Terms and our Refund Policy.`,
  },
  {
    title: "14. Modifications, Termination & Contact",
    body: `We may update these Terms with notice via the Service or email for material changes. Continued use after the effective date constitutes acceptance. We may terminate or suspend access for breach, non-payment, fraudulent refund or chargeback activity, or legal requirement. Upon termination, licenses to evaluation content end; provisions that by nature should survive will remain in effect. Support: ${LEGAL_SUPPORT_EMAIL} · General: ${LEGAL_CONTACT_EMAIL} · Legal: ${LEGAL_LEGAL_EMAIL} · ${COMPANY_NAME} · ${LEGAL_LOCATION_STATEMENT}.`,
  },
];

export const COPYRIGHT_NOTICE = `© ${new Date().getFullYear()} ${COMPANY_NAME}. All rights reserved. ${PRODUCT_NAME} is developed and operated by ${COMPANY_NAME}. Part of the ${GROUP_NAME}.`;
