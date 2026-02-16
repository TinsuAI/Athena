import type { NextConfig } from "next";

const API_BACKEND_URL =
  process.env.API_BACKEND_URL || "http://localhost:8980";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    return {
      // beforeFiles runs before Next.js filesystem routes (including API routes).
      // We use specific patterns for FastAPI /api/auth/* endpoints so they
      // don't collide with NextAuth's catch-all at /api/auth/[...nextauth].
      beforeFiles: [
        { source: "/api/auth/login", destination: `${API_BACKEND_URL}/api/auth/login` },
        { source: "/api/auth/register", destination: `${API_BACKEND_URL}/api/auth/register` },
        { source: "/api/auth/forgot-password", destination: `${API_BACKEND_URL}/api/auth/forgot-password` },
        { source: "/api/auth/reset-password", destination: `${API_BACKEND_URL}/api/auth/reset-password` },
      ],
      afterFiles: [],
      // fallback runs after all filesystem and dynamic routes, so
      // NextAuth's /api/auth/[...nextauth] catch-all is matched first.
      // Unmatched /api/* routes (admin, search, browse, etc.) go to FastAPI.
      fallback: [
        { source: "/api/:path*", destination: `${API_BACKEND_URL}/api/:path*` },
      ],
    };
  },
};

export default nextConfig;
