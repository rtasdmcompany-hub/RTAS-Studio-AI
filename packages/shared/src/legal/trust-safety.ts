import type { LegalSection } from "./types";
import { COMPANY_NAME, LEGAL_LAST_UPDATED, PRODUCT_NAME } from "./terms";

export const TRUST_SAFETY_INTRO = `${PRODUCT_NAME} is designed for original, authorized creative production — music videos, commercials, social content, animation, and original AI characters. We prohibit face swapping, celebrity impersonation, identity fraud, deepfake abuse, unauthorized voice cloning, political manipulation, and illegal content. This page summarizes our Trust & Safety commitments for creators, partners, and payment networks.`;

export const TRUST_SAFETY_SECTIONS: LegalSection[] = [
  {
    title: "1. Our commitment",
    body: `${COMPANY_NAME} operates ${PRODUCT_NAME} as a professional AI video studio. We expect every user to generate only original content, licensed content, content they own, or content they are authorized to use. Identity Preservation tools exist solely to keep an authorized likeness consistent across scenes — never to impersonate third parties.`,
  },
  {
    title: "2. Strictly prohibited",
    body: `The following uses are forbidden on ${PRODUCT_NAME}. Violations may result in immediate suspension, content removal, and cooperation with payment partners or authorities where required.`,
    bullets: [
      "Face swapping or face replacement onto other people",
      "Celebrity impersonation or cloning of public figures",
      "Identity fraud or deceptive likeness of real people without authorization",
      "Deepfake abuse intended to deceive, harass, or defraud",
      "Unauthorized voice cloning of real people",
      "Political manipulation, election interference, or synthetic propaganda",
      "Illegal content, exploitation of minors, hate, or harassment",
      "Any content that infringes publicity, privacy, or intellectual-property rights",
    ],
  },
  {
    title: "3. Authorized Identity Preservation",
    body: `When you enable Identity Preservation (also called User Identity Consistency), you must upload only reference media that depicts you, your original character, or a person who has given you explicit permission. Typing consent confirmation in the Studio affirms that authorization. We do not market or support celebrity generators, clone-person workflows, or deepfake products.`,
  },
  {
    title: "4. Reporting & enforcement",
    body: `Report suspected abuse to support@rtasdigital.com with links, job IDs, or screenshots. We may disable accounts, withhold downloads, and preserve logs for investigation. Related policies: Terms of Service (/terms), AI Usage Policy (/ai-policy), Privacy Policy (/privacy).`,
  },
  {
    title: "5. Updates",
    body: `We may update this Trust & Safety page as laws, payment-network rules, and model-provider policies evolve. Material changes will be reflected with a revised date. Last updated: ${LEGAL_LAST_UPDATED}.`,
  },
];
