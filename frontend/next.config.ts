import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    domains: ["cdn.islamic.network"],
  },
  reactStrictMode: false, // 👈 add this line
  webpack(config) {
    config.module.rules.push({
      test: /\.svg$/i,
      issuer: /\.[jt]sx?$/,
      use: ["@svgr/webpack"],

    });
    return config;
  },
};

export default nextConfig;
