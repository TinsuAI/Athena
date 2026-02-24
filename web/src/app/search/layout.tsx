/**
 * Search layout — server-side auth gate.
 * Fetches site settings and redirects unauthenticated users when search_requires_auth=true.
 */
import { redirect } from "next/navigation";
import { auth } from "@/lib/auth";

const API_URL =
  process.env.API_BACKEND_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8980";

async function fetchSearchRequiresAuth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_URL}/api/settings`, {
      cache: "no-store",
    });
    if (!res.ok) return true; // fail-safe
    const data = await res.json();
    return data?.data?.search_requires_auth !== "false";
  } catch {
    return true; // fail-safe on network error
  }
}

export default async function SearchLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const requiresAuth = await fetchSearchRequiresAuth();

  if (requiresAuth) {
    const session = await auth();
    if (!session) {
      redirect("/login?callbackUrl=/search");
    }
  }

  return <>{children}</>;
}
