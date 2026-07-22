import {
  COMPANY_NAME,
  LEGAL_ENTITY_STATEMENT,
  LEGAL_LAST_UPDATED,
  PRODUCT_NAME,
} from "./terms";
import type { LegalSection } from "./types";

export const REFUND_INTRO = `${LEGAL_ENTITY_STATEMENT} This Refund Policy explains how refunds, cancellations, and chargebacks work for ${PRODUCT_NAME} purchases. ${COMPANY_NAME} supplies the software; Paddle.com Market Limited (and its affiliates, "Paddle") is the Merchant of Record that sells the product to you, collects payment, and processes refunds. Last updated: ${LEGAL_LAST_UPDATED}.`;

export const REFUND_SECTIONS: LegalSection[] = [
  {
    title: "1. Merchant of Record (Paddle)",
    body: `All paid plans, subscriptions, and credit packs for ${PRODUCT_NAME} are sold by Paddle as Merchant of Record (MoR), not by ${COMPANY_NAME} as the payment seller. That means:`,
    bullets: [
      "Paddle is the legal seller of the purchase to you",
      "Payment is collected by Paddle; Paddle appears on your bank or card statement (often with our product name)",
      "Paddle calculates and remits applicable sales tax, VAT, or GST and issues the official invoice/receipt",
      "Refunds and payment disputes for the purchase are handled by Paddle under Paddle's Buyer Terms and Refund Policy",
      `${COMPANY_NAME} does not receive your card details for checkout and does not pay refunds directly to your card or wallet`,
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
    title: "3. Digital services & credit consumption",
    body: `${PRODUCT_NAME} delivers digital AI generation capacity (credits measured in seconds of output). Once generation starts or credits are consumed, the digital service has been performed. Except where mandatory consumer-protection law requires otherwise, Transactions are generally non-refundable and non-exchangeable after delivery or use — consistent with Paddle's global refund approach for digital products. Short-term starter plans (for example Tester / Creator Starter) that unlock a credit allotment in your account are treated as delivered digital goods once that allotment is available, unless a technical fault prevented access entirely.`,
  },
  {
    title: "4. When refunds may be available",
    body: `Refunds are decided and issued by Paddle, not paid out of ${COMPANY_NAME}'s bank account to you. Without limiting your mandatory consumer rights, refunds may be available where:`,
    bullets: [
      "Applicable law gives you a statutory cooling-off / withdrawal right (for example, certain EU/UK consumer digital-content rules — windows and waivers are set out in Paddle's Refund Policy)",
      "Paddle grants a discretionary refund (Paddle may consider requests submitted within fourteen (14) days of the Transaction date; a request within that period does not guarantee approval)",
      "There is a duplicate charge, billing error, or you were charged after a cancellation that had already taken effect",
      "There is evidence of a material technical or product defect that prevents access as described, after reasonable attempts to resolve it",
    ],
  },
  {
    title: "5. How to request a refund (contact Paddle)",
    body: `Because Paddle is the seller and holds the payment, request refunds and manage billing through Paddle:`,
    bullets: [
      "Use the “View receipt” or “Manage subscription” link in your Paddle transaction confirmation email",
      "Visit https://paddle.net and select the option to request a refund (or cancel a subscription)",
      "Provide your purchase email, order/receipt ID, and reason when prompted",
    ],
  },
  {
    title: "6. Product support from RTAS (not card refunds)",
    body: `For product access, account, or generation issues, contact ${COMPANY_NAME} at contact@rtasstudio.com or support@rtasstudio.com. We can help troubleshoot and, where appropriate, share context with Paddle. We cannot reverse a card charge ourselves. If you have a persistent technical defect that blocks use of what you paid for, contact us first; if unresolved, escalate the refund request to Paddle with details of the issue (as described in Paddle's Refund Policy section on technical or product defects).`,
  },
  {
    title: "7. Subscriptions & cancellations",
    body: `You may cancel a subscription at any time through Paddle (receipt / manage-subscription links or https://paddle.net) to stop future renewals. Cancellation typically takes effect at the end of the current billing period and does not, by itself, create a refund for the period already paid — unless required by law or approved by Paddle. Unused credits in a paid period are not automatically cashed out.`,
  },
  {
    title: "8. Chargebacks & payment disputes",
    body: `Please contact Paddle (and, for product issues, contact@rtasstudio.com) before filing a chargeback or bank dispute. Premature chargebacks can delay resolution; Paddle may suspend access to the Product while a chargeback is reviewed. This does not limit rights you may have under card-scheme or consumer-protection rules.`,
  },
  {
    title: "9. Processing time",
    body: `If Paddle approves a refund, Paddle processes it to your original payment method where possible, typically within fourteen (14) days of approval. Your bank or card network may take additional time to post the credit.`,
  },
  {
    title: "10. Contact",
    body: `Product & account support: contact@rtasstudio.com · support@rtasstudio.com. Website: https://rtasstudio.com. Billing, receipts, cancellations, and refund requests for paid Transactions: https://paddle.net and the links in your Paddle receipt email. Related documents: Terms of Service (/terms), Privacy Policy (/privacy), Paddle Refund Policy (https://www.paddle.com/legal/refund-policy).`,
  },
];
