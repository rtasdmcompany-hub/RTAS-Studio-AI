import {
  PREMIUM_PRICE_USD,
  STANDARD_PRICE_USD,
  TESTER_PRICE_USD,
} from "../credits";
import type { LegalSection } from "./types";

export const COMPANY_NAME = "RTAS DIGITAL MARKETING COMPANY";
export const GROUP_NAME = "RTAS GROUP OF COMPANIES";
export const PRODUCT_NAME = "RTAS STUDIO AI";

export const LEGAL_JURISDICTION = "Pakistan";

export const LEGAL_ENTITY_STATEMENT = `${PRODUCT_NAME} is a proprietary software division under ${GROUP_NAME}. The Service is developed, operated, and licensed by ${COMPANY_NAME} (registered / operating in ${LEGAL_JURISDICTION}) on behalf of the Group.`;

export const LEGAL_LAST_UPDATED = "22 July 2026";

export const TERMS_INTRO = `${LEGAL_ENTITY_STATEMENT} These Terms of Service ("Terms") govern your access to and use of the ${PRODUCT_NAME} platform, including web applications, APIs, generated media, and related support services (collectively, the "Service"). By creating an account, purchasing credits or a subscription, or otherwise using the Service, you enter a binding agreement with ${COMPANY_NAME}. If you do not agree, you must discontinue use immediately.`;

export const TERMS_SECTIONS: LegalSection[] = [
  {
    title: "1. Corporate Entity & Proprietary Software",
    body: `${LEGAL_ENTITY_STATEMENT} All intellectual property in the Service — including source code, models orchestration, user interfaces, workflows, branding, documentation, and derivative tooling — is owned exclusively by ${COMPANY_NAME} and its affiliates within ${GROUP_NAME}. Except for the limited licenses expressly granted in these Terms, no title or ownership interest is transferred to you. Reverse engineering, redistribution, or creation of competing services from the Service is prohibited unless permitted by mandatory law.`,
  },
  {
    title: "2. Agreement to Terms & Eligibility",
    body: `By accessing the Service you confirm that you are at least the age of digital consent in your jurisdiction (typically 16–18, or 13 with verifiable parental consent where applicable), that you have authority to bind any organization on whose behalf you register, and that you agree to these Terms, our Privacy Policy, and Cookie Policy. Enterprise or agency accounts must ensure end-user compliance.`,
  },
  {
    title: "3. Service Description & AI Processing",
    body: `${PRODUCT_NAME} provides AI-assisted video generation from text, lyrics, images, voice, and related inputs, including Authorized Identity Preservation ("Identity Consistency") workflows for user-owned or authorized likenesses only. The Service is marketed for text-to-video, image-to-video, marketing videos, commercials, social content, music videos, animation, original AI characters, talking avatars with lip sync on authorized media, and related editing tools. Output quality, latency, and availability depend on your subscription tier, fair-use limits, and third-party model providers. We may modify features, models, or capacity with reasonable notice where practicable.`,
  },
  {
    title: "4. Subscription Plans, Credits & Billing Cycles",
    body: `Paid tiers include Creator Starter (Pay-As-You-Go, USD ${TESTER_PRICE_USD} one-time evaluation access), Pro Studio Tier (USD ${STANDARD_PRICE_USD}/month), and Production Enterprise (USD ${PREMIUM_PRICE_USD}/month), each granting generation credits where one (1) credit equals one (1) second of rendered video unless otherwise stated at checkout. Monthly credits reset at the end of each billing period; early renewal may roll unused credits forward per in-app rules. Prices are listed in United States Dollars unless your checkout session displays local currency via our payment partners.`,
    bullets: [
      "Creator Starter: evaluation-tier output (including watermarked exports where applicable).",
      "Pro Studio Tier: 1080p HD masters, clean exports, and commercial download licensing.",
      "Production Enterprise: 4K cinematic masters with priority+ Identity Preservation queuing.",
    ],
  },
  {
    title: "5. Payment Terms & Refund Policies Managed via Worldwide Merchant Networks",
    body: `Card, wallet, and local payment methods are processed by our Merchant of Record ("MoR"), Paddle, which is the legal seller of paid ${PRODUCT_NAME} purchases to you. Paddle calculates applicable sales tax, VAT, or GST, issues compliant invoices/receipts, screens for fraud, and handles buyer refunds and chargebacks under Paddle's Buyer Terms and Refund Policy. ${COMPANY_NAME} does not store full payment card numbers on its servers and does not pay card refunds directly. Settlement to ${COMPANY_NAME} follows Paddle's payout schedule. Except where mandatory consumer-protection law requires otherwise, Transactions are generally non-refundable after delivery or credit use. For refunds, cancellations, and receipt lookups, use your Paddle confirmation email or https://paddle.net. Contact Paddle (and, for product issues, contact@rtasstudio.com) before filing a chargeback. See our Refund Policy at https://rtasstudio.com/refund and Paddle's Refund Policy at https://www.paddle.com/legal/refund-policy.`,
  },
  {
    title: "6. Commercial Licensing & Download Rights",
    body: `Active paid subscribers on Pro Studio Tier or Production Enterprise receive a worldwide, non-exclusive license to commercially exploit AI-generated outputs they lawfully create through the Service, including public performance, advertising, and client delivery, provided: (a) you comply with these Terms; (b) you own or hold valid licenses for all inputs (likeness, voice, music, trademarks, and training data); and (c) you respect third-party AI provider acceptable-use policies. Creator Starter and non-subscribed preview outputs remain for private evaluation only unless upgraded. ${COMPANY_NAME} grants no rights beyond this scope.`,
  },
  {
    title: "7. Free Previews, Watermarks & Evaluation Content",
    body: `Watermarked or preview-tier exports are licensed solely for private review within the Service. You may not remove, obscure, or circumvent watermarks, commercially distribute preview content, broadcast it, or monetize screen recordings containing evaluation marks. Upgrading to a paid tier with clean-export entitlements is required before public or commercial release.`,
  },
  {
    title: "8. User Content, Representations & IP Indemnity",
    body: `You retain ownership of lawful uploads. You grant ${COMPANY_NAME} a limited, worldwide license to host, process, transmit, and transform uploads solely to operate, secure, and improve the Service. You represent that your inputs and published outputs do not infringe third-party rights, violate publicity or privacy laws, or breach platform policies. You agree to indemnify ${COMPANY_NAME} and ${GROUP_NAME} affiliates against claims arising from your content or misuse, to the extent permitted by law.`,
  },
  {
    title: "9. AI Output Disclaimer & Identity Preservation Limitations",
    body: `Generative AI may produce inaccurate, offensive, or unintended resemblance to third-party works or persons. Authorized Identity Preservation / User Identity Consistency tooling improves consistency across scenes for likenesses you own or are authorized to use; it does not constitute face swapping, celebrity cloning, or a deepfake product, and it does not guarantee perfect likeness or legal clearance for commercial likeness use. You are solely responsible for reviewing, clearing, and approving all outputs before publication or monetization. See also our Trust & Safety page (/trust-safety) and AI Usage Policy (/ai-policy).`,
  },
  {
    title: "10. Prohibited Uses & Acceptable Use Policy",
    body: `You may not use the Service for illegal activity, harassment, hate speech, exploitation of minors, malware distribution, sanctions evasion, or infringement of intellectual property or personality rights. In particular, the following are strictly prohibited. We may suspend or terminate accounts, preserve evidence, and cooperate with law enforcement, regulators, or our Merchant of Record where required.`,
    bullets: [
      "Face swapping, face replacement, or any workflow that maps one person's face onto another.",
      "Celebrity cloning, celebrity generators, or impersonation of public figures.",
      "Identity theft, identity fraud, or deceptive synthetic media of real people without authorization.",
      "Deepfake generation intended to mislead, defraud, harass, or harm.",
      "Voice cloning of real people without their permission.",
      "Fraud, scams, political manipulation, or illegal content.",
      "No generation of sexual content involving minors or non-consenting individuals.",
      "No automated scraping or API abuse beyond documented rate limits.",
    ],
  },
  {
    title: "11. Privacy, Data Processing & Cross-Border Transfers",
    body: `Personal data is processed as described in our Privacy Policy. By using the Service you acknowledge that data may be transferred to the United States, European Union, United Kingdom, Pakistan, and other regions where we or subprocessors operate, subject to appropriate safeguards where required by GDPR, UK GDPR, or comparable frameworks.`,
  },
  {
    title: "12. International Compliance, Governing Law & Dispute Resolution",
    body: `These Terms are governed by the laws of ${LEGAL_JURISDICTION}, without regard to conflict-of-law rules, except where mandatory consumer protections in your country of residence require otherwise. Nothing in these Terms limits non-waivable rights under EU, UK, Australian, Canadian, or other consumer-protection statutes. Disputes should first be addressed to contact@rtasstudio.com; where arbitration or courts are permitted, you agree to individual resolution and waive class actions to the extent enforceable.`,
  },
  {
    title: "13. Limitation of Liability & Warranty Disclaimer",
    body: `THE SERVICE IS PROVIDED "AS IS" AND "AS AVAILABLE." TO THE MAXIMUM EXTENT PERMITTED BY LAW, ${COMPANY_NAME} AND ${GROUP_NAME} AFFILIATES DISCLAIM IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT. NEITHER ${COMPANY_NAME} NOR ITS AFFILIATES SHALL BE LIABLE FOR INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, OR LOST PROFITS. AGGREGATE LIABILITY SHALL NOT EXCEED THE FEES YOU PAID TO ${COMPANY_NAME} IN THE TWELVE (12) MONTHS PRECEDING THE CLAIM.`,
  },
  {
    title: "14. Modifications, Termination & Contact",
    body: `We may update these Terms with notice via the Service or email for material changes. Continued use after the effective date constitutes acceptance. We may terminate or suspend access for breach, non-payment, or legal requirement. Upon termination, licenses to evaluation content end; provisions that by nature should survive will remain in effect. Legal, billing, and compliance inquiries: contact@rtasstudio.com · ${COMPANY_NAME} · ${GROUP_NAME}. Last updated: ${LEGAL_LAST_UPDATED}.`,
  },
];

export const COPYRIGHT_NOTICE = `© ${new Date().getFullYear()} ${COMPANY_NAME}. All rights reserved. ${PRODUCT_NAME} is a proprietary software division under ${GROUP_NAME}.`;
