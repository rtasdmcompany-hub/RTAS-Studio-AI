import {
  COMPANY_NAME,
  LEGAL_ENTITY_STATEMENT,
  LEGAL_LAST_UPDATED,
  PRODUCT_NAME,
} from "./terms";
import type { LegalSection } from "./types";

export const REFUND_INTRO = `${LEGAL_ENTITY_STATEMENT} This Refund Policy explains when ${COMPANY_NAME} and our Merchant-of-Record (MoR) partners may issue refunds for ${PRODUCT_NAME} purchases. Last updated: ${LEGAL_LAST_UPDATED}.`;

export const REFUND_SECTIONS: LegalSection[] = [
  {
    title: "1. Merchant of Record",
    body: `Paid plans and credit packs for ${PRODUCT_NAME} are sold through our Merchant of Record, Paddle (and comparable MoR processors if configured). Paddle appears on your bank or card statement, calculates applicable tax, and issues the official invoice/receipt. Refund requests are reviewed under this Policy and Paddle's consumer rules for your country.`,
  },
  {
    title: "2. Digital services & credit consumption",
    body: `${PRODUCT_NAME} delivers digital AI generation capacity (credits measured in seconds of output). Once generation starts or credits are consumed, the digital service has been performed. Except where mandatory consumer-protection law requires otherwise, fees are generally non-refundable after a billing period begins or after credits are used.`,
  },
  {
    title: "3. When we may approve a refund",
    body: `We may approve a full or partial refund (or equivalent credit) in good faith where:`,
    bullets: [
      "A duplicate charge occurred for the same plan/period",
      "You were billed after a confirmed cancellation took effect before the renewal date",
      "A verified platform outage prevented you from using paid credits for a material portion of the billing period",
      "Mandatory local law grants a cooling-off or withdrawal right that applies to your purchase",
    ],
  },
  {
    title: "4. Tester / short-term plans",
    body: `Short-term starter plans (for example Tester) grant a limited credit allotment for a short validity window. After purchase confirmation, these are treated as consumed digital goods once the allotment is available in your account, unless a technical fault prevented access entirely.`,
  },
  {
    title: "5. How to request a refund",
    body: `Email support@rtasdigital.com within sixty (60) days of the charge and include: account email, MoR receipt/transaction ID, plan name, date of charge, and a short reason. Do not open a chargeback before contacting support — premature chargebacks may delay resolution and can lead to account suspension for fraud risk.`,
  },
  {
    title: "6. Processing time",
    body: `Approved refunds are processed by the MoR to your original payment method. Bank timing varies by country and card network (often 5–15 business days after approval).`,
  },
  {
    title: "7. Contact",
    body: `Billing & refunds: support@rtasdigital.com. Website: https://rtasstudio.com. Related documents: Terms of Service (/terms) and Privacy Policy (/privacy).`,
  },
];
