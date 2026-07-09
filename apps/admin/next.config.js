/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ["@rtas/shared"],
  images: { unoptimized: true },
  eslint: { ignoreDuringBuilds: true },
};

module.exports = nextConfig;
