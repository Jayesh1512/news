import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Produces .next/standalone for a minimal, self-contained Docker image.
  // See frontend/Dockerfile.
  output: "standalone",
};

export default nextConfig;
