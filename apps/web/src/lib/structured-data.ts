import {
  PREMIUM_CREDITS,
  PREMIUM_PRICE_USD,
  PRODUCT_NAME,
  STANDARD_CREDITS,
  STANDARD_PRICE_USD,
  TESTER_CREDITS,
  TESTER_DURATION_DAYS,
  TESTER_PRICE_USD,
} from "@rtas/shared";
import { SITE_METADATA_DESCRIPTION, SITE_OG_IMAGE_URL } from "@/lib/site-metadata";
import { SITE_SUPPORT_EMAIL } from "@/lib/site-links";
import { SITE_URL } from "@/lib/site-url";

const LOGO_URL = `${SITE_URL}/rtas-logo.png`;

export function organizationSchema() {
  return {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: PRODUCT_NAME,
    legalName: "RTAS Digital Marketing Company",
    url: SITE_URL,
    logo: LOGO_URL,
    image: SITE_OG_IMAGE_URL,
    email: SITE_SUPPORT_EMAIL,
    sameAs: [
      "https://www.youtube.com/@RTASDigital",
      "https://www.facebook.com/RTASDigital",
      "https://www.instagram.com/rtasdigital",
      "https://www.linkedin.com/company/rtas-digital",
      "https://x.com/RTASDigital",
      "https://github.com/rtasdmcompany-hub/RTAS-Studio-AI",
    ],
    contactPoint: [
      {
        "@type": "ContactPoint",
        contactType: "customer support",
        email: SITE_SUPPORT_EMAIL,
        availableLanguage: ["English"],
        url: `${SITE_URL}/help/contact`,
      },
    ],
  };
}

export function websiteSchema() {
  return {
    "@context": "https://schema.org",
    "@type": "WebSite",
    name: PRODUCT_NAME,
    url: SITE_URL,
    description: SITE_METADATA_DESCRIPTION,
    inLanguage: "en-US",
    publisher: {
      "@type": "Organization",
      name: PRODUCT_NAME,
      logo: LOGO_URL,
    },
    potentialAction: {
      "@type": "SearchAction",
      target: {
        "@type": "EntryPoint",
        urlTemplate: `${SITE_URL}/help?q={search_term_string}`,
      },
      "query-input": "required name=search_term_string",
    },
  };
}

export function softwareApplicationSchema() {
  return {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name: PRODUCT_NAME,
    applicationCategory: "MultimediaApplication",
    operatingSystem: "Web",
    url: SITE_URL,
    description: SITE_METADATA_DESCRIPTION,
    image: SITE_OG_IMAGE_URL,
    offers: {
      "@type": "AggregateOffer",
      url: `${SITE_URL}/pricing`,
      priceCurrency: "USD",
      lowPrice: String(TESTER_PRICE_USD),
      highPrice: String(PREMIUM_PRICE_USD),
      offerCount: 3,
      availability: "https://schema.org/InStock",
      offers: [
        {
          "@type": "Offer",
          name: "Creator Starter (Tester)",
          price: String(TESTER_PRICE_USD),
          priceCurrency: "USD",
          url: `${SITE_URL}/pricing`,
          description: `${TESTER_CREDITS} seconds for ${TESTER_DURATION_DAYS} days. 1 credit = 1 second.`,
          category: "one_time",
        },
        {
          "@type": "Offer",
          name: "Pro Studio (Standard)",
          price: String(STANDARD_PRICE_USD),
          priceCurrency: "USD",
          url: `${SITE_URL}/pricing`,
          description: `${STANDARD_CREDITS} seconds per month. 1 credit = 1 second.`,
          category: "subscription",
        },
        {
          "@type": "Offer",
          name: "Production Enterprise (Premium 4K)",
          price: String(PREMIUM_PRICE_USD),
          priceCurrency: "USD",
          url: `${SITE_URL}/pricing`,
          description: `${PREMIUM_CREDITS} seconds per month with cinematic 4K capacity. 1 credit = 1 second.`,
          category: "subscription",
        },
      ],
    },
    publisher: {
      "@type": "Organization",
      name: "RTAS Digital Marketing Company",
      logo: LOGO_URL,
    },
  };
}

/** Product + Offer graph for the pricing page (commercial visibility). */
export function pricingProductSchema() {
  return {
    "@context": "https://schema.org",
    "@type": "Product",
    name: PRODUCT_NAME,
    description: SITE_METADATA_DESCRIPTION,
    brand: {
      "@type": "Brand",
      name: PRODUCT_NAME,
    },
    url: `${SITE_URL}/pricing`,
    image: SITE_OG_IMAGE_URL,
    offers: {
      "@type": "AggregateOffer",
      priceCurrency: "USD",
      lowPrice: String(TESTER_PRICE_USD),
      highPrice: String(PREMIUM_PRICE_USD),
      offerCount: 3,
      availability: "https://schema.org/InStock",
      url: `${SITE_URL}/pricing`,
    },
  };
}

export function breadcrumbSchema(
  items: Array<{ name: string; path: string }>
) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, index) => ({
      "@type": "ListItem",
      position: index + 1,
      name: item.name,
      item: `${SITE_URL}${item.path.startsWith("/") ? item.path : `/${item.path}`}`,
    })),
  };
}

export function faqSchema(
  items: Array<{ question: string; answer: string }>
) {
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: items.map((item) => ({
      "@type": "Question",
      name: item.question,
      acceptedAnswer: {
        "@type": "Answer",
        text: item.answer,
      },
    })),
  };
}
