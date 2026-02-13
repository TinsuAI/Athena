"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navLinks = [
  { href: "/search", label: "Search" },
  { href: "/browse", label: "Browse" },
  { href: "/lookups", label: "Lookups" },
];

export function Header() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 bg-[#0f172a] border-b border-white/[0.06] shadow-[0_2px_12px_rgba(0,0,0,0.15)]">
      <div className="max-w-[1600px] w-full mx-auto px-3 sm:px-7 flex items-center justify-between h-12 sm:h-16">
        <div className="flex items-center gap-2.5 sm:gap-4">
          <Link href="/" className="flex items-center gap-2 sm:gap-2.5 group">
            <div className="w-[30px] h-[30px] sm:w-[34px] sm:h-[34px] bg-gradient-to-br from-emerald-500 to-emerald-700 rounded-md flex items-center justify-center font-mono text-white font-extrabold text-[13px] sm:text-[15px] tracking-tighter shadow-[0_2px_8px_rgba(5,150,105,0.3)]">
              HS
            </div>
            <div>
              <div className="text-sm sm:text-base font-bold text-white tracking-tight">
                Athena
              </div>
              <div className="hidden sm:block text-[11px] text-slate-400 font-medium tracking-wider uppercase">
                HS Code Lookup
              </div>
            </div>
          </Link>

          <div className="w-px h-5 sm:h-7 bg-white/10" />

          <nav
            className="flex items-center gap-1.5 sm:gap-2 text-[12px] sm:text-[13px]"
            aria-label="Main navigation"
          >
            {navLinks.map((link, i) => {
              const isActive =
                pathname === link.href ||
                (pathname?.startsWith(link.href + "/") ?? false);
              return (
                <span key={link.href} className="flex items-center gap-1.5 sm:gap-2">
                  {i > 0 && (
                    <span className="text-white/20 text-[10px] sm:text-[11px]">&#9656;</span>
                  )}
                  <Link
                    href={link.href}
                    className={
                      isActive
                        ? "text-white/85 font-semibold"
                        : "text-white/50 hover:text-emerald-400 transition-colors duration-150"
                    }
                  >
                    {link.label}
                  </Link>
                </span>
              );
            })}
          </nav>
        </div>
      </div>
    </header>
  );
}
