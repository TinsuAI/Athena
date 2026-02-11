"use client";

import Link from "next/link";

export function Header() {
  return (
    <header className="border-b">
      <div className="container mx-auto flex h-16 items-center px-4">
        <Link href="/" className="text-xl font-bold">
          Athena
        </Link>
        <nav className="ml-auto flex gap-4">
          <Link href="/search" className="text-sm font-medium">
            Search
          </Link>
          <Link href="/browse" className="text-sm font-medium">
            Browse
          </Link>
          <Link href="/lookups" className="text-sm font-medium">
            Lookups
          </Link>
        </nav>
      </div>
    </header>
  );
}
