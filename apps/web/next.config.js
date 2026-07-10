/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: [
    "@rtas/shared",
    "@rtas/ui",
    "@rtas/design-tokens",
    "@rtas/utils",
    "@rtas/hooks",
    "@rtas/icons",
  ],
  // Mitigates Next.js Image Optimizer DoS advisories (GHSA-9g9p-9gw9-jx7f, GHSA-h64f-5h5j-jqjh).
  // Full CVE clearance for remaining Next 14.x advisories requires Next 15/16 (breaking).
  images: {
    unoptimized: true,
    remotePatterns: [],
  },
  compress: true,
  // Slow local / constrained CI workers can exceed the default 60s page-data budget.
  staticPageGenerationTimeout: 180,
  eslint: { ignoreDuringBuilds: false },
  typescript: { ignoreBuildErrors: false },
  experimental: {
    outputFileTracingExcludes: {
      "/api/compile": ["../backend/**"],
    },
  },
  poweredByHeader: false,
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()",
          },
          {
            key: "Content-Security-Policy-Report-Only",
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.paddle.com https://*.paddle.com https://accounts.google.com",
              "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
              "img-src 'self' data: blob: https:",
              "font-src 'self' data: https://fonts.gstatic.com",
              "connect-src 'self' https://*.supabase.co https://api.fal.ai https://queue.fal.run https://api.resend.com https://*.paddle.com https://accounts.google.com",
              "frame-src 'self' https://*.paddle.com https://accounts.google.com",
              "media-src 'self' blob: https:",
              "object-src 'none'",
              "base-uri 'self'",
              "form-action 'self' https://*.paddle.com",
              "frame-ancestors 'none'",
            ].join("; "),
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
