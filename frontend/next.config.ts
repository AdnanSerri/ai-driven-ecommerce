import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  turbopack: {
    root: __dirname,
  },
  images: {
    localPatterns: [
      {
        pathname: "/api/image-proxy",
      },
    ],
    remotePatterns: [
      {
        protocol: "http",
        hostname: "localhost",
        port: "8000",
      },
      {
        protocol: "https",
        hostname: "**",
      },
    ],
  },
};

export default nextConfig;
