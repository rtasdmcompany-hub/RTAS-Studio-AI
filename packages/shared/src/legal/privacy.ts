import { COMPANY_NAME, GROUP_NAME, LEGAL_LAST_UPDATED, PRODUCT_NAME } from "./terms";

export const PRIVACY_SECTIONS = [
  {
    title: "1. Data Controller",
    body: `${COMPANY_NAME}, under ${GROUP_NAME}, operates ${PRODUCT_NAME}. We process personal data to provide the Service, billing, and support.`,
  },
  {
    title: "2. Data We Collect",
    body: `Account information (name, email), usage data (credits, generations, preferences), payment metadata from our Merchant of Record (we do not store full card numbers), uploaded assets for video generation, and technical logs (IP, device, browser) for security.`,
  },
  {
    title: "3. How We Use Data",
    body: `To operate the Service, process subscriptions, prevent fraud, improve AI workflows, comply with law, and communicate service updates. AI providers may process prompts and uploads per their policies.`,
  },
  {
    title: "4. International Transfers",
    body: `Data may be processed in the United States, European Union, Pakistan, or other regions where we or our subprocessors host infrastructure. We use appropriate safeguards where required.`,
  },
  {
    title: "5. Retention",
    body: `We retain account data while your account is active and as needed for legal obligations. You may request deletion subject to billing and legal retention requirements.`,
  },
  {
    title: "6. Your Rights",
    body: `Depending on your jurisdiction, you may have rights to access, correct, delete, or port your data, and to object to certain processing. Contact support@rtasdigital.com.`,
  },
  {
    title: "7. Security",
    body: `We implement administrative and technical measures to protect data. No method of transmission is 100% secure; use strong passwords and protect your account credentials.`,
  },
  {
    title: "8. Children",
    body: `The Service is not directed to children under 13 (or higher age where required). We do not knowingly collect children's data without parental consent.`,
  },
  {
    title: "9. Contact",
    body: `Privacy inquiries: support@rtasdigital.com · ${COMPANY_NAME} · ${GROUP_NAME}. Last updated: ${LEGAL_LAST_UPDATED}.`,
  },
];
