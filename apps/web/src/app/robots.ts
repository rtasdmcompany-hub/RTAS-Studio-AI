import type { MetadataRoute } from "next";

const CANONICAL = "https://rtasstudio.com";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: [
          "/api/",
          "/auth/",
          "/admin",
          "/admin/",
          "/profile",
          "/profile/",
          "/studio",
          "/studio/",
          "/share/",
        ],
      },
    ],
    sitemap: `${CANONICAL}/sitemap.xml`,
    host: CANONICAL,
  };
}
