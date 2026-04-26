import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  turbopack: {
    root: "..",
  },
  serverExternalPackages: [
    "@blocknote/xl-ai",
  ],
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8070/api/:path*",
      },
    ];
  },
};

export default nextConfig;
