import {
  COMPANY_NAME,
  LEGAL_CONTACT_EMAIL,
  LEGAL_ENTITY_STATEMENT,
  LEGAL_LOCATION_STATEMENT,
  LEGAL_SUPPORT_EMAIL,
  PRODUCT_NAME,
} from "./terms";
import type { LegalSection } from "./types";

export const COMMUNITY_GUIDELINES_INTRO = `${LEGAL_ENTITY_STATEMENT} These Community Guidelines set expectations for respectful, lawful use of ${PRODUCT_NAME} — including Studio, sharing features, feedback channels, Discord (if linked), and support interactions. They complement our Terms of Service (including Acceptable Use in §10), Trust & Safety, and AI Usage Policy. Violations may lead to content removal, feature limits, or account suspension.`;

export const COMMUNITY_GUIDELINES_SECTIONS: LegalSection[] = [
  {
    title: "1. Be Authorized & Honest",
    body: `Only submit content and likenesses you own or are authorized to use. Identity Preservation workflows are for authorized subjects only. Do not impersonate others, misrepresent affiliation with ${COMPANY_NAME}, or claim certifications (SOC 2, ISO, “GDPR certified,” etc.) that the product has not obtained.`,
  },
  {
    title: "2. No Harmful or Illegal Content",
    body: `Do not use the Service to create or distribute content that is illegal, that exploits minors, that facilitates fraud or harassment, or that violates our Trust & Safety prohibitions (including face-swap misuse, unauthorized deepfakes, and celebrity cloning).`,
  },
  {
    title: "3. Respect People & Support Channels",
    body: `Treat other users, partners, and support staff with respect. Do not spam feedback forms, abuse ticket systems, or share others' personal data without permission. Threats, hate speech, and coordinated harassment are prohibited.`,
  },
  {
    title: "4. Fair Use of Capacity",
    body: `Credits and concurrent render slots are finite. Do not attempt to bypass rate limits, share accounts to evade plan limits, scrape the Service, or attack infrastructure. Report genuine outages via Help Center or the public Status page rather than flooding support.`,
  },
  {
    title: "5. Feedback & Public Discussion",
    body: `Product feedback is welcome. When discussing ${PRODUCT_NAME} publicly, do not disclose other users' private data, unpublished security vulnerabilities (email ${LEGAL_SUPPORT_EMAIL} or ${LEGAL_CONTACT_EMAIL} privately first), or confidential enterprise materials.`,
  },
  {
    title: "6. Enforcement",
    body: `We may warn, restrict features, remove content, or suspend accounts based on severity and history. Appeals: ${LEGAL_SUPPORT_EMAIL} with your account email and relevant ticket or job IDs. These Guidelines do not create contractual rights beyond our Terms.`,
  },
  {
    title: "7. Contact",
    body: `Support: ${LEGAL_SUPPORT_EMAIL} · General: ${LEGAL_CONTACT_EMAIL} · ${COMPANY_NAME} · ${LEGAL_LOCATION_STATEMENT}. Related: Trust & Safety, AI Usage Policy, Terms of Service, Copyright & DMCA.`,
  },
];
