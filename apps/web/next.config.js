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
        ],
      },
    ];
  },
};

module.exports = nextConfig;
