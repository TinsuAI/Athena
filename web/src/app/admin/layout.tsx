"use client";

import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { data: session, status } = useSession();
  const router = useRouter();
  const role = (session?.user as { role?: string })?.role;

  useEffect(() => {
    if (status === "authenticated" && role !== "admin") {
      const timer = setTimeout(() => router.push("/search"), 2000);
      return () => clearTimeout(timer);
    }
  }, [status, role, router]);

  if (status === "loading") {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-slate-400 text-sm">Loading...</div>
      </div>
    );
  }

  if (role !== "admin") {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-slate-900">Access Denied</h1>
          <p className="text-slate-500 mt-2">
            You do not have admin privileges.
          </p>
          <p className="text-slate-400 text-sm mt-1">
            Redirecting to search...
          </p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
