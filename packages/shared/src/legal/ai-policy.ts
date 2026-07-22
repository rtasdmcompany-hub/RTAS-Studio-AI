import type { LegalSection } from "./types";
import {
  COMPANY_NAME,
  LEGAL_CONTACT_EMAIL,
  LEGAL_ENTITY_STATEMENT,
  LEGAL_LOCATION_STATEMENT,
  LEGAL_SUPPORT_EMAIL,
  PRODUCT_NAME,
} from "./terms";

export const AI_POLICY_INTRO = `${LEGAL_ENTITY_STATEMENT} This AI Usage Policy explains how you may use generative features in ${PRODUCT_NAME}. By using the Service you agree to generate only original content, licensed content, content you own, or content you are authorized to use — and to follow our Trust & Safety rules and Terms of Service.`;

export const AI_POLICY_SECTIONS: LegalSection[] = [
  {
    title: "1. Permitted generation",
    body: `You may use ${PRODUCT_NAME} to create:`,
    bullets: [
      "Original scripts, scenes, characters, and videos you invent",
      "Marketing videos, product commercials, and social media content you are authorized to publish",
      "Music videos and performance videos using rights you control (or have licensed)",
      "AI animation, anime, and 3D / original AI characters",
      "Talking avatars and lip sync for user-owned or authorized media",
      "Upscaling, background removal, enhancement, and AI editing of assets you own or may lawfully process",
      "Identity Preservation / User Identity Consistency for likenesses you own or are authorized to use",
    ],
  },
  {
    title: "2. Required authorization",
    body: `Before uploading a likeness, voice, logo, track, or brand asset, you must own it or hold a valid license / release. Identity Preservation requires affirmative consent in the Studio that the reference belongs to you or an authorized subject. You are solely responsible for clearing rights before commercial use. Credits consumed for generation are computational resources under your plan (Tester, Standard, or Premium) and do not transfer ownership of third-party rights.`,
  },
  {
    title: "3. Prohibited AI uses",
    body: `${COMPANY_NAME} prohibits using the Service for:`,
    bullets: [
      "Face swapping or replacing another person's face",
      "Celebrity cloning or impersonation of real public figures",
      "Identity theft or deceptive synthetic media of real people without consent",
      "Deepfake generation intended to mislead, defraud, or harm",
      "Voice cloning without the speaker's permission",
      "Fraud, scams, or social-engineering content",
      "Political manipulation and illegal or abusive content",
    ],
  },
  {
    title: "4. Model providers, billing & network rules",
    body: `Generation may run on third-party AI providers. Output quality and speed depend on GPU availability and load. You must also comply with those providers' acceptable-use policies and with card-network / Merchant of Record (Paddle) rules applicable to digital goods. ${PRODUCT_NAME} may refuse, throttle, or remove jobs that appear to violate this Policy. Misuse may result in account suspension and is not eligible for refund under our Refund Policy.`,
  },
  {
    title: "5. Related documents & contact",
    body: `See Trust & Safety (/trust-safety), Terms of Service (/terms), Privacy Policy (/privacy), Refund Policy (/refund), and Cookie Policy (/cookies). Support: ${LEGAL_SUPPORT_EMAIL} · ${LEGAL_CONTACT_EMAIL} · ${COMPANY_NAME} · ${LEGAL_LOCATION_STATEMENT}.`,
  },
];
