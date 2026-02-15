/**
 * Next.js 16 proxy for route protection.
 * Redirects unauthenticated users to /login for protected routes.
 */

export { auth as default } from "@/lib/auth";

export const config = {
  matcher: ["/favorites/:path*", "/history/:path*", "/admin/:path*"],
};
