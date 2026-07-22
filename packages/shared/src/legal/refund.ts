import {
  PREMIUM_CREDITS,
  PREMIUM_PRICE_USD,
  STANDARD_CREDITS,
  STANDARD_PRICE_USD,
  TESTER_CREDITS,
  TESTER_DURATION_DAYS,
  TESTER_PRICE_USD,
} from "../credits";
import {
  COMPANY_NAME,
  LEGAL_CONTACT_EMAIL,
  LEGAL_ENTITY_STATEMENT,
  LEGAL_LOCATION_STATEMENT,
  LEGAL_SUPPORT_EMAIL,
  PRODUCT_NAME,
} from "./terms";
import type { LegalSection } from "./types";

export const REFUND_INTRO = `${LEGAL_ENTITY_STATEMENT} This Refund Policy explains how refunds, cancellations, and chargebacks work for ${PRODUCT_NAME} purchases. ${COMPANY_NAME} develops and operates the software; Paddle.com Market Limited (and its affiliates, "Paddle") is the Merchant of Record (MoR) that sells the product to you, collects payment, calculates applicable taxes, and processes refunds.`;

export const REFUND_SECTIONS: LegalSection[] = [
  {
    title: "1. Merchant of Record (Paddle)",
    body: `All paid plans, subscriptions, and Credit packs for ${PRODUCT_NAME} are sold by Paddle as Merchant of Record, not by ${COMPANY_NAME} as the payment seller. That means:`,
    bullets: [
      "Paddle is the legal seller of the purchase to you.",
      "Payment is collected by Paddle; Paddle appears on your bank or card statement (often with our product name).",
      "Paddle calculates and remits applicable sales tax, VAT, or GST and issues the official invoice/receipt.",
      "Refunds and payment disputes for the purchase are handled by Paddle under Paddle's Buyer Terms and Refund Policy.",
      `${COMPANY_NAME} does not receive your card details for checkout and does not pay refunds directly to your card or wallet.`,
    ],
  },
  {
    title: "2. How this Policy relates to Paddle",
    body: `This page describes how ${PRODUCT_NAME} works as a digital service and how we cooperate with Paddle on billing issues. For the binding buyer refund and withdrawal rules that apply to your Transaction, see Paddle's documents (as updated by Paddle from time to time):`,
    bullets: [
      "Paddle Refund Policy: https://www.paddle.com/legal/refund-policy",
      "Paddle Checkout Buyer Terms: https://www.paddle.com/legal/checkout-buyer-terms",
      "Paddle buyer support (receipts, cancel, request refund): https://paddle.net",
    ],
  },
  {
    title: "3. Plans, Credits & digital delivery",
    body: `${PRODUCT_NAME} delivers digital AI generation capacity. Credits are computational AI resources — not ownership of media, not a cash wallet, and not a transferable property interest beyond use of the Service under our Terms. One (1) Credit equals one (1) second of rendered video unless otherwise stated at checkout. Once generation starts or Credits are consumed, the digital service has been performed. Except where mandatory consumer-protection law requires otherwise, Transactions are generally non-refundable and non-exchangeable after delivery or use — consistent with Paddle's approach for digital products.`,
    bullets: [
      `Tester: USD ${TESTER_PRICE_USD} · ${TESTER_CREDITS} Credits · ${TESTER_DURATION_DAYS}-day access — treated as delivered digital goods once the Credit allotment is available in your account, unless a technical fault prevented access entirely.`,
      `Standard: USD ${STANDARD_PRICE_USD}/month · ${STANDARD_CREDITS} Credits per billing period.`,
      `Premium: USD ${PREMIUM_PRICE_USD}/month · ${PREMIUM_CREDITS} Credits per billing period.`,
      "Taxes (sales tax, VAT, GST) are calculated by Paddle at checkout.",
      "Generation speed depends on GPU availability and load; queue time alone is not a refundable defect.",
    ],
  },
  {
    title: "4. When refunds may be available",
    body: `Refunds are decided and issued by Paddle, not paid out of ${COMPANY_NAME}'s bank account to you. Without limiting your mandatory consumer rights, refunds may be available where:`,
    bullets: [
      "Applicable law gives you a statutory cooling-off / withdrawal right (for example, certain EU/UK consumer digital-content rules — windows and waivers are set out in Paddle's Refund Policy).",
      "Paddle grants a discretionary refund (Paddle may consider requests submitted within fourteen (14) days of the Transaction date; a request within that period does not guarantee approval).",
      "There is a duplicate charge, billing error, or you were charged after a cancellation that had already taken effect.",
      "There is evidence of a material technical or product defect that prevents access as described, after reasonable attempts to resolve it.",
    ],
  },
  {
    title: "5. What is not a refundable defect",
    body: `The following do not, by themselves, entitle you to a refund (except where mandatory law requires otherwise):`,
    bullets: [
      "Artistic preference, stylistic taste, or subjective dissatisfaction with AI-generated output.",
      "Third-party outages or degradation of cloud, GPU, model-provider, CDN, or payment infrastructure — no automatic refund.",
      "Violations of our Terms of Service, AI Usage Policy, or Trust & Safety rules — including refunds requested after misuse.",
      "Unused Credits remaining at the end of a billing period (unused Credits are not automatically cashed out).",
      "Plan upgrades or downgrades that immediately change billing or Credit allotments according to checkout and account rules.",
    ],
  },
  {
    title: "6. How to request a refund (contact Paddle)",
    body: `Because Paddle is the seller and holds the payment, request refunds and manage billing through Paddle:`,
    bullets: [
      "Use the “View receipt” or “Manage subscription” link in your Paddle transaction confirmation email.",
      "Visit https://paddle.net and select the option to request a refund (or cancel a subscription).",
      "Provide your purchase email, order/receipt ID, and reason when prompted.",
    ],
  },
  {
    title: "7. Product support from RTAS (not card refunds)",
    body: `For product access, account, or generation issues, contact ${COMPANY_NAME} at ${LEGAL_SUPPORT_EMAIL} or ${LEGAL_CONTACT_EMAIL}. We can help troubleshoot and, where appropriate, share context with Paddle. We cannot reverse a card charge ourselves. If you have a persistent technical defect that blocks use of what you paid for, contact us first; if unresolved, escalate the refund request to Paddle with details of the issue (as described in Paddle's Refund Policy section on technical or product defects).`,
  },
  {
    title: "8. Subscriptions, cancellations, upgrades & downgrades",
    body: `You may cancel a subscription at any time through Paddle (receipt / manage-subscription links or https://paddle.net) to stop future renewals. Cancellation typically takes effect at the end of the current billing period and does not, by itself, create a refund for the period already paid — unless required by law or approved by Paddle. Upgrades and downgrades may take effect immediately and may adjust billing and Credits. Unused Credits in a paid period are not automatically cashed out.`,
  },
  {
    title: "9. Fraudulent refunds, chargebacks & account action",
    body: `Fraudulent or abusive refund requests may result in suspension or termination of your ${PRODUCT_NAME} account. Please contact Paddle (and, for product issues, ${LEGAL_SUPPORT_EMAIL} or ${LEGAL_CONTACT_EMAIL}) before filing a chargeback or bank dispute. Premature chargebacks can delay resolution. While a chargeback or payment dispute is investigated, access to the Product may be temporarily suspended. This does not limit rights you may have under card-scheme or consumer-protection rules.`,
  },
  {
    title: "10. Processing time",
    body: `If Paddle approves a refund, Paddle processes it to your original payment method where possible, typically within fourteen (14) days of approval. Your bank or card network may take additional time to post the credit.`,
  },
  {
    title: "11. Contact",
    body: `Product & account support: ${LEGAL_SUPPORT_EMAIL} · ${LEGAL_CONTACT_EMAIL}. Website: https://rtasstudio.com. ${COMPANY_NAME} · ${LEGAL_LOCATION_STATEMENT}. Billing, receipts, cancellations, and refund requests for paid Transactions: https://paddle.net and the links in your Paddle receipt email. Related documents: Terms of Service (/terms), Privacy Policy (/privacy), Cookie Policy (/cookies), Paddle Refund Policy (https://www.paddle.com/legal/refund-policy).`,
  },
];
