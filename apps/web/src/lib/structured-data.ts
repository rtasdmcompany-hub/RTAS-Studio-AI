import { PRODUCT_NAME } from "@rtas/shared";
import { SITE_METADATA_DESCRIPTION, SITE_OG_IMAGE_URL } from "@/lib/site-metadata";
import { SITE_SUPPORT_EMAIL } from "@/lib/site-links";
import { SITE_URL } from "@/lib/site-url";

export function organizationSchema() {
  return {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: PRODUCT_NAME,
    legalName: "RTAS Digital Marketing Company",
    url: SITE_URL,
    logo: SITE_OG_IMAGE_URL,
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
    publisher: {
      "@type": "Organization",
      name: PRODUCT_NAME,
      logo: SITE_OG_IMAGE_URL,
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
    offers: {
      "@type": "Offer",
      url: `${SITE_URL}/pricing`,
      priceCurrency: "USD",
      availability: "https://schema.org/InStock",
    },
    publisher: {
      "@type": "Organization",
      name: PRODUCT_NAME,
      logo: SITE_OG_IMAGE_URL,
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
