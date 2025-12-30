import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export", // Static HTML export for Cloudflare Pages
  reactCompiler: true,
  images: {
    unoptimized: true, // Required for static export
  },
  // Trailing slashes for cleaner URLs
  trailingSlash: true,
};

export default nextConfig;
