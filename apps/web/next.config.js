/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ["@rtas/shared"],
  images: { unoptimized: true },
  eslint: { ignoreDuringBuilds: true },
  typescript: { ignoreBuildErrors: false },
  experimental: {
    outputFileTracingExcludes: {
      "/api/compile": ["../backend/**"],
    },
  },
};

module.exports = nextConfig;
