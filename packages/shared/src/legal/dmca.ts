import {
  COMPANY_NAME,
  LEGAL_CONTACT_EMAIL,
  LEGAL_ENTITY_STATEMENT,
  LEGAL_LEGAL_EMAIL,
  LEGAL_LOCATION_STATEMENT,
  LEGAL_SUPPORT_EMAIL,
  PRODUCT_NAME,
} from "./terms";
import type { LegalSection } from "./types";

export const DMCA_INTRO = `${LEGAL_ENTITY_STATEMENT} This Copyright & DMCA Policy explains how ${COMPANY_NAME} handles notices of alleged copyright infringement relating to ${PRODUCT_NAME}. It is provided for operational clarity and does not constitute legal advice. Where U.S. DMCA safe-harbor procedures are invoked by a rights holder, we follow a notice-and-takedown workflow consistent with our Terms of Service and Trust & Safety rules.`;

export const DMCA_SECTIONS: LegalSection[] = [
  {
    title: "1. Scope",
    body: `This Policy covers allegedly infringing material hosted or displayed through ${PRODUCT_NAME} (including user-submitted assets and generated outputs stored in connection with an account). Payment disputes and Merchant of Record refunds are handled by Paddle under its Buyer Terms — not this Policy.`,
  },
  {
    title: "2. Designated Contact",
    body: `Send copyright complaints and counter-notices to our designated contact:`,
    bullets: [
      `Email (preferred): ${LEGAL_LEGAL_EMAIL}`,
      `Copy (optional): ${LEGAL_CONTACT_EMAIL} · ${LEGAL_SUPPORT_EMAIL}`,
      `Operator: ${COMPANY_NAME} · ${LEGAL_LOCATION_STATEMENT}`,
      "Subject line: Copyright / DMCA Notice — RTAS Studio AI",
    ],
  },
  {
    title: "3. Notice Requirements",
    body: `To help us act promptly, include as much of the following as practicable:`,
    bullets: [
      "Your full name, mailing address, telephone number, and email address.",
      "A description of the copyrighted work you claim is infringed.",
      "The exact URL(s), job ID(s), project name(s), or other location of the allegedly infringing material on our Service.",
      "A statement that you have a good-faith belief the use is not authorized by the copyright owner, its agent, or the law.",
      "A statement, under penalty of perjury where applicable, that the information in the notice is accurate and that you are the owner or authorized to act on the owner's behalf.",
      "Your physical or electronic signature (typing your full legal name is acceptable for email).",
    ],
  },
  {
    title: "4. Our Process",
    body: `Upon receiving a substantially complete notice, we may: (a) acknowledge receipt; (b) remove or disable access to the material while we review; (c) notify the account holder; and (d) request additional information if the notice is incomplete. We may refuse to act on notices that are abusive, incomplete, or clearly fraudulent. Repeat infringers may have accounts suspended or terminated under our Terms.`,
  },
  {
    title: "5. Counter-Notice",
    body: `If your content was removed and you believe the removal was mistaken or that you have authorization to use the material, email ${LEGAL_LEGAL_EMAIL} with a counter-notice including your contact details, identification of the removed material, a good-faith statement that the material was removed by mistake or misidentification, and consent to the jurisdiction stated in our Terms (or mandatory consumer venue where required). We may forward the counter-notice to the complainant and restore material where appropriate after a waiting period, unless the complainant notifies us of a court action.`,
  },
  {
    title: "6. User-Generated & AI Content",
    body: `${PRODUCT_NAME} generates media from user inputs. Users are solely responsible for ensuring they have all rights and authorizations for prompts, images, likenesses, music, and other inputs. Unauthorized use of third-party IP, celebrity likenesses, or protected works may result in removal and account action under Trust & Safety and Terms §10 (Acceptable Use).`,
  },
  {
    title: "7. Related Policies & Contact",
    body: `See also Terms of Service, Trust & Safety, AI Usage Policy, and Community Guidelines. Copyright: ${LEGAL_LEGAL_EMAIL} · Support: ${LEGAL_SUPPORT_EMAIL} · General: ${LEGAL_CONTACT_EMAIL} · ${COMPANY_NAME} · ${LEGAL_LOCATION_STATEMENT}.`,
  },
];
