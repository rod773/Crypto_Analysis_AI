import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: process.env.NEXT_STATIC_EXPORT === "true" ? "export" : undefined,
  images: { unoptimized: true },
  trailingSlash: true,
};

export default nextConfig;
