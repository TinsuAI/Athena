"use client";

import Link from "next/link";

export function Sidebar() {
  return (
    <aside className="w-64 border-r bg-muted/40 p-4">
      <nav className="flex flex-col gap-2">
        <Link
          href="/search"
          className="rounded-md px-3 py-2 text-sm font-medium hover:bg-accent"
        >
          Search
        </Link>
        <Link
          href="/favorites"
          className="rounded-md px-3 py-2 text-sm font-medium hover:bg-accent"
        >
          Favorites
        </Link>
        <Link
          href="/history"
          className="rounded-md px-3 py-2 text-sm font-medium hover:bg-accent"
        >
          History
        </Link>
      </nav>
    </aside>
  );
}
