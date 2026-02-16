"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSession, signOut } from "next-auth/react";
import { useStore } from "@/lib/store";
import { Menu, X, Search, BookOpen, ClipboardList, Shield, LogOut, LogIn, UserPlus } from "lucide-react";

const navLinks = [
  { href: "/search", label: "Tìm kiếm", icon: Search },
  { href: "/browse", label: "Biểu thuế", icon: BookOpen },
  { href: "/lookups", label: "Tra cứu", icon: ClipboardList },
];

export function Header() {
  const pathname = usePathname();
  const { data: session, status } = useSession();
  const logout = useStore((s) => s.logout);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Close menu on route change
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [pathname]);

  // Lock body scroll when menu is open
  useEffect(() => {
    if (mobileMenuOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileMenuOpen]);

  const handleLogout = useCallback(() => {
    try {
      logout();
      signOut({ callbackUrl: "/login" });
    } catch (error) {
      console.error("Logout error:", error);
      signOut({ callbackUrl: "/login" });
    }
  }, [logout]);

  const isAdmin = (session?.user as { role?: string } | undefined)?.role === "admin";

  return (
    <>
      <header className="sticky top-0 z-50 bg-[#0f172a] border-b border-white/[0.06] shadow-[0_2px_12px_rgba(0,0,0,0.15)]">
        <div className="max-w-[1600px] w-full mx-auto px-3 sm:px-7 flex items-center justify-between h-12 sm:h-16">
          {/* Logo + Desktop Nav */}
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
                  Tra cứu mã HS
                </div>
              </div>
            </Link>

            {/* Desktop nav — hidden on mobile */}
            <div className="hidden md:flex items-center gap-2 sm:gap-4">
              <div className="w-px h-5 sm:h-7 bg-white/10" />
              <nav
                className="flex items-center gap-1.5 sm:gap-2 text-[12px] sm:text-[13px]"
                aria-label="Điều hướng chính"
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

          {/* Desktop auth — hidden on mobile */}
          <div className="hidden md:flex items-center gap-2 sm:gap-3 text-[12px] sm:text-[13px]">
            {status === "loading" ? (
              <span className="text-white/30" aria-live="polite" aria-busy="true">
                Đang tải...
              </span>
            ) : session?.user ? (
              <>
                {isAdmin && (
                  <Link
                    href="/admin"
                    className={
                      pathname?.startsWith("/admin")
                        ? "text-emerald-400 font-semibold"
                        : "text-white/50 hover:text-emerald-400 transition-colors duration-150"
                    }
                  >
                    Quản trị
                  </Link>
                )}
                <span className="text-white/60 truncate max-w-[160px]">
                  {session.user.email}
                </span>
                <button
                  onClick={handleLogout}
                  className="text-white/50 hover:text-emerald-400 transition-colors duration-150"
                >
                  Đăng xuất
                </button>
              </>
            ) : (
              <>
                <Link
                  href="/login"
                  className="text-white/50 hover:text-emerald-400 transition-colors duration-150"
                >
                  Đăng nhập
                </Link>
                <Link
                  href="/register"
                  className="rounded-md bg-emerald-600 px-3 py-1.5 text-white font-medium hover:bg-emerald-500 transition-colors duration-150"
                >
                  Đăng ký
                </Link>
              </>
            )}
          </div>

          {/* Mobile hamburger button */}
          <button
            onClick={() => setMobileMenuOpen((prev) => !prev)}
            className="md:hidden relative w-9 h-9 flex items-center justify-center rounded-lg text-white/70 hover:text-white hover:bg-white/[0.08] active:bg-white/[0.12] transition-all duration-200"
            aria-label={mobileMenuOpen ? "Đóng menu" : "Mở menu"}
            aria-expanded={mobileMenuOpen}
          >
            <span
              className={`absolute transition-all duration-300 ${
                mobileMenuOpen ? "rotate-90 scale-0 opacity-0" : "rotate-0 scale-100 opacity-100"
              }`}
            >
              <Menu size={20} strokeWidth={2.2} />
            </span>
            <span
              className={`absolute transition-all duration-300 ${
                mobileMenuOpen ? "rotate-0 scale-100 opacity-100" : "-rotate-90 scale-0 opacity-0"
              }`}
            >
              <X size={20} strokeWidth={2.2} />
            </span>
          </button>
        </div>
      </header>

      {/* Mobile menu overlay + panel */}
      {/* Backdrop */}
      <div
        className={`md:hidden fixed inset-0 z-40 bg-black/60 backdrop-blur-sm transition-opacity duration-300 ${
          mobileMenuOpen ? "opacity-100" : "opacity-0 pointer-events-none"
        }`}
        style={{ top: "48px" }}
        onClick={() => setMobileMenuOpen(false)}
        aria-hidden="true"
      />

      {/* Slide-down panel */}
      <div
        className={`md:hidden fixed left-0 right-0 z-40 transition-all duration-300 ease-[cubic-bezier(0.32,0.72,0,1)] ${
          mobileMenuOpen
            ? "translate-y-0 opacity-100"
            : "-translate-y-4 opacity-0 pointer-events-none"
        }`}
        style={{ top: "48px" }}
        role="dialog"
        aria-modal="true"
        aria-label="Menu điều hướng"
      >
        <div className="bg-[#0f172a] border-b border-white/[0.06] shadow-[0_16px_48px_rgba(0,0,0,0.4)]">
          {/* Emerald accent line */}
          <div className="h-[2px] bg-gradient-to-r from-emerald-500/0 via-emerald-500 to-emerald-500/0" />

          <nav className="px-4 pt-3 pb-2" aria-label="Menu di động">
            {navLinks.map((link, i) => {
              const isActive =
                pathname === link.href ||
                (pathname?.startsWith(link.href + "/") ?? false);
              const Icon = link.icon;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`flex items-center gap-3 px-3 py-3 rounded-lg text-[14px] font-medium transition-all duration-200 ${
                    isActive
                      ? "bg-emerald-500/[0.12] text-emerald-400"
                      : "text-white/60 hover:text-white hover:bg-white/[0.05] active:bg-white/[0.08]"
                  }`}
                  style={{
                    animationDelay: mobileMenuOpen ? `${i * 50}ms` : "0ms",
                  }}
                >
                  <Icon
                    size={18}
                    strokeWidth={isActive ? 2.2 : 1.8}
                    className={isActive ? "text-emerald-400" : "text-white/40"}
                  />
                  <span>{link.label}</span>
                  {isActive && (
                    <div className="ml-auto w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  )}
                </Link>
              );
            })}

            {/* Admin link for admin users */}
            {isAdmin && (
              <Link
                href="/admin"
                className={`flex items-center gap-3 px-3 py-3 rounded-lg text-[14px] font-medium transition-all duration-200 ${
                  pathname?.startsWith("/admin")
                    ? "bg-emerald-500/[0.12] text-emerald-400"
                    : "text-white/60 hover:text-white hover:bg-white/[0.05] active:bg-white/[0.08]"
                }`}
              >
                <Shield
                  size={18}
                  strokeWidth={pathname?.startsWith("/admin") ? 2.2 : 1.8}
                  className={pathname?.startsWith("/admin") ? "text-emerald-400" : "text-white/40"}
                />
                <span>Quản trị</span>
                {pathname?.startsWith("/admin") && (
                  <div className="ml-auto w-1.5 h-1.5 rounded-full bg-emerald-400" />
                )}
              </Link>
            )}
          </nav>

          {/* Divider */}
          <div className="mx-4 h-px bg-white/[0.06]" />

          {/* Auth section */}
          <div className="px-4 pt-2 pb-4">
            {status === "loading" ? (
              <div className="px-3 py-3 text-[13px] text-white/30">
                Đang tải...
              </div>
            ) : session?.user ? (
              <>
                {/* User info */}
                <div className="flex items-center gap-3 px-3 py-3">
                  <div className="w-8 h-8 rounded-full bg-emerald-600/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400 text-[12px] font-bold uppercase">
                    {session.user.email?.charAt(0) ?? "U"}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="text-[13px] text-white/80 font-medium truncate">
                      {session.user.email}
                    </div>
                    <div className="text-[11px] text-white/30 mt-0.5">
                      {isAdmin ? "Quản trị viên" : "Người dùng"}
                    </div>
                  </div>
                </div>

                <button
                  onClick={handleLogout}
                  className="flex items-center gap-3 w-full px-3 py-3 rounded-lg text-[14px] font-medium text-white/50 hover:text-red-400 hover:bg-red-500/[0.08] active:bg-red-500/[0.12] transition-all duration-200"
                >
                  <LogOut size={18} strokeWidth={1.8} className="text-white/30" />
                  <span>Đăng xuất</span>
                </button>
              </>
            ) : (
              <div className="flex flex-col gap-2 pt-1">
                <Link
                  href="/login"
                  className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-[14px] font-medium text-white/70 border border-white/[0.1] hover:border-white/[0.2] hover:text-white hover:bg-white/[0.04] active:bg-white/[0.08] transition-all duration-200"
                >
                  <LogIn size={16} strokeWidth={2} />
                  Đăng nhập
                </Link>
                <Link
                  href="/register"
                  className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-[14px] font-semibold text-white bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 transition-all duration-200 shadow-[0_2px_8px_rgba(5,150,105,0.25)]"
                >
                  <UserPlus size={16} strokeWidth={2} />
                  Đăng ký
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
