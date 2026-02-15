"use client";

/**
 * Client-side providers wrapper.
 * Required for NextAuth.js useSession() in client components.
 */

import { SessionProvider } from "next-auth/react";

export function Providers({ children }: { children: React.ReactNode }) {
  return <SessionProvider>{children}</SessionProvider>;
}
