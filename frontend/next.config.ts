import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // keep Turbopack enabled
  turbopack: {},

  reactStrictMode: false,
  images: {
    domains: ["cdn.islamic.network"],
  },

  // Webpack override for SVGR
  webpack(config, { isServer }) {
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
