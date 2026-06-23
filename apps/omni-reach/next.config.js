/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ["@rtas/shared"],
  eslint: { ignoreDuringBuilds: true },
  typescript: { ignoreBuildErrors: false },
};

module.exports = nextConfig;
