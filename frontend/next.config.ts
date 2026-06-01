import type { NextConfig } from "next";

const nextConfig: NextConfig = {
   output: "standalone",
  // keep Turbopack enabled
  turbopack: {},

  reactStrictMode: false,
    // ── YEH 2 BLOCKS ADD KARO ──
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  // ── BUS ITNA ──
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "cdn.islamic.network",
        port: "",
        pathname: "/**",
      },
    ],
  },

  // Webpack override for SVGR
  webpack(config, { isServer } )  {
    // Only modify webpack if Turbopack is not in use
    config.module.rules.push({
      test: /\.svg$/i,
      issuer: /\.[jt]sx?$/,
      use: ["@svgr/webpack"],
    });

    return config;
  },
};

export default nextConfig;
