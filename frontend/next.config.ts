import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
   images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "img.icons8.com",
      },
    ],
  },
};

export default nextConfig;
