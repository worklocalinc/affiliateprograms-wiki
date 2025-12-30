import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactCompiler: true,
  images: {
    unoptimized: true, // Required for Cloudflare Pages
  },
};

export default nextConfig;
