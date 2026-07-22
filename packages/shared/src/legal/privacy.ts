import {
  COMPANY_NAME,
  GROUP_NAME,
  LEGAL_ENTITY_STATEMENT,
  LEGAL_LAST_UPDATED,
  PRODUCT_NAME,
} from "./terms";
import type { LegalSection } from "./types";

export const PRIVACY_INTRO = `${LEGAL_ENTITY_STATEMENT} This Privacy Policy explains how ${COMPANY_NAME} ("we," "us," or "Controller") collects, uses, stores, and protects personal data when you use ${PRODUCT_NAME} websites, applications, and related services worldwide. We design our practices to align with GDPR (EU/EEA), UK GDPR, CCPA/CPRA (California), PIPEDA (Canada), and comparable international privacy frameworks.`;

export const PRIVACY_SECTIONS: LegalSection[] = [
  {
    title: "1. Corporate Entity & Data Controller",
    body: `${LEGAL_ENTITY_STATEMENT} For privacy purposes, ${COMPANY_NAME} acts as the data controller for account, billing, and Service usage data described below. Payment card data is processed by our Merchant-of-Record partners acting as independent controllers or processors for checkout. Contact: contact@rtasstudio.com.`,
  },
  {
    title: "2. Personal Data We Collect & Lawful Bases",
    body: `We collect only data necessary to operate a global SaaS platform. Lawful bases under GDPR include contract performance, legitimate interests (security, fraud prevention, product improvement), legal obligation, and consent where required (e.g., non-essential cookies).`,
    bullets: [
      "Account data: name, email address, authentication identifiers (including OAuth tokens from Google sign-in).",
      "Subscription & billing metadata: plan tier, credit balance, transaction IDs, tax jurisdiction — not full card numbers.",
      "Studio content: prompts, lyrics, uploaded images, voice references, and generation parameters you submit.",
      "Generated outputs: video files, thumbnails, share links, and export history associated with your account.",
      "Technical & security logs: IP address, device type, browser, timestamps, and diagnostic events.",
    ],
  },
  {
    title: "3. Data Retention & AI Models",
    body: `We retain personal data only as long as necessary for the purposes described in this Policy. Account profile data is kept while your account remains active and for a reasonable period thereafter to resolve disputes or comply with law. Studio uploads and generation parameters are retained to deliver the Service, enable re-downloads, and maintain Identity Preservation continuity across projects unless you delete them or close your account. Aggregated, de-identified analytics may be retained indefinitely. AI model providers engaged as subprocessors may temporarily cache inputs for inference; their retention schedules are governed by their own enterprise data-processing terms. You may request deletion subject to billing records, fraud-prevention, and statutory retention requirements (typically up to seven years for tax and accounting records where applicable).`,
  },
  {
    title: "4. How We Use, Share & Process Personal Data",
    body: `We use personal data to authenticate users, allocate credits, render AI video, provide customer support, send service announcements, detect abuse, and comply with legal requests. We do not sell personal data. We share data with subprocessors under contractual safeguards, including cloud hosting, email delivery, AI inference providers, analytics (if consented), and worldwide merchant networks for payments.`,
  },
  {
    title: "5. International Transfers & Cross-Border Safeguards",
    body: `Because ${PRODUCT_NAME} serves users globally, data may be processed in the United States, European Union, United Kingdom, Pakistan, and other countries where we or our subprocessors maintain infrastructure. Where required, we implement Standard Contractual Clauses (SCCs), UK International Data Transfer Addenda, or equivalent mechanisms, and assess transfer risks in line with Schrems II guidance.`,
  },
  {
    title: "6. Your Global Privacy Rights",
    body: `Depending on your jurisdiction, you may have the right to access, rectify, erase, restrict, or port your personal data, and to object to certain processing or automated decision-making. California residents may have rights to know, delete, and opt out of "sale" or "sharing" (we do not sell personal data). EU/EEA and UK users may lodge complaints with their local supervisory authority. To exercise rights, email contact@rtasstudio.com with sufficient identity verification. We respond within applicable statutory timelines (typically 30–45 days).`,
  },
  {
    title: "7. Security Measures & Incident Response",
    body: `We implement administrative, technical, and organizational measures including access controls, encryption in transit (TLS), authenticated sessions, and monitoring for anomalous activity. No method of transmission or storage is completely secure; you are responsible for safeguarding credentials. If a personal-data breach poses risk to your rights, we will notify you and regulators as required by applicable law.`,
  },
  {
    title: "8. Children's Privacy",
    body: `The Service is not directed to children under 13 (or under 16 in certain jurisdictions). We do not knowingly collect personal data from children without verifiable parental consent. If you believe a child has provided data, contact contact@rtasstudio.com and we will delete it promptly.`,
  },
  {
    title: "9. Policy Updates, Cookies & Contact",
    body: `Material changes to this Policy will be posted on this page with an updated "Last updated" date. Non-essential cookies and similar technologies are described in our Cookie Policy. Privacy inquiries: contact@rtasstudio.com · ${COMPANY_NAME} · ${GROUP_NAME}. Last updated: ${LEGAL_LAST_UPDATED}.`,
  },
];
