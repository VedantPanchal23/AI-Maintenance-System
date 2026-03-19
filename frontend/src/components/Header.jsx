"use client";

import { useAuthStore, useAlertStore, useThemeStore } from "@/lib/store";
import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import { cn } from "@/lib/utils";
import {
  BellIcon,
  ArrowRightOnRectangleIcon,
  Bars3Icon,
  SunIcon,
  MoonIcon,
  HomeIcon,
  CpuChipIcon,
  BellAlertIcon,
  ChartBarIcon,
  WrenchScrewdriverIcon,
  BeakerIcon,
  CogIcon,
} from "@heroicons/react/24/outline";

const navigation = [
  { name: "Dashboard",   href: "/dashboard",   icon: HomeIcon },
  { name: "Equipment",   href: "/equipment",   icon: CpuChipIcon },
  { name: "Alerts",      href: "/alerts",      icon: BellAlertIcon },
  { name: "Analytics",   href: "/analytics",   icon: ChartBarIcon },
  { name: "Maintenance", href: "/maintenance", icon: WrenchScrewdriverIcon },
  { name: "ML Models",   href: "/ml-admin",    icon: BeakerIcon },
  { name: "Settings",    href: "/settings",    icon: CogIcon },
];

export default function Header({ onMenuToggle }) {
  const { user, logout } = useAuthStore();
  const { activeAlerts, fetchActiveAlerts } = useAlertStore();
  const { theme, toggleTheme } = useThemeStore();
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    fetchActiveAlerts();
    const interval = setInterval(fetchActiveAlerts, 30000);
    return () => clearInterval(interval);
  }, [fetchActiveAlerts]);

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <header className="sticky top-0 z-30 flex flex-col justify-center min-h-[5rem] bg-white/80 dark:bg-[#020617]/80 backdrop-blur-xl border-b border-slate-200/60 dark:border-white/[0.04] transition-colors duration-500">
      <div className="flex items-center justify-between px-4 lg:px-8 w-full max-w-7xl mx-auto gap-4">
        {/* Left: Brand & Mobile Menu */}
        <div className="flex shrink-0 items-center gap-3">
          {onMenuToggle && (
            <button
              onClick={onMenuToggle}
              className="lg:hidden p-2 -ml-2 rounded-xl hover:bg-slate-100 dark:hover:bg-white/[0.04] transition-colors"
              aria-label="Open menu"
            >
              <Bars3Icon className="h-5 w-5 text-slate-500 dark:text-slate-400" />
            </button>
          )}
          <Link href="/dashboard" className="flex items-center gap-2.5 group">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-500 shadow-glow-blue transition-shadow group-hover:shadow-lg">
              <CpuChipIcon className="h-4 w-4 text-white" />
            </div>
            <div className="hidden sm:block leading-tight">
              <p className="text-[0.9rem] font-bold text-slate-900 dark:text-white tracking-tight">Predictive AI</p>
              {user?.organization_name && (
                <p className="text-[0.7rem] text-slate-500 dark:text-slate-400 font-medium">
                  {user.organization_name}
                </p>
              )}
            </div>
          </Link>
        </div>

        {/* Center: Desktop Navigation */}
        <nav className="hidden lg:flex flex-1 justify-center items-center gap-1 xl:gap-2 px-2 overflow-x-auto no-scrollbar snap-x">
          {navigation.map((item) => {
            const active = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center gap-2 px-3 py-2 rounded-xl text-[0.875rem] font-bold tracking-wide transition-all duration-300 whitespace-nowrap snap-center shrink-0",
                  active
                    ? "bg-slate-100 dark:bg-white/[0.08] text-slate-900 dark:text-white shadow-sm dark:shadow-[inset_0_1px_0_0_rgba(255,255,255,0.02)]"
                    : "text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-white/[0.04] hover:text-slate-900 dark:hover:text-slate-200"
                )}
              >
                <item.icon className={cn(
                  "h-[1.125rem] w-[1.125rem] shrink-0 transition-colors",
                  active ? "text-brand-500 dark:text-brand-400" : "text-slate-400"
                )} />
                {item.name}
              </Link>
            );
          })}
        </nav>

        {/* Right: Actions */}
        <div className="flex shrink-0 items-center justify-end gap-2 xl:gap-3">
          {/* Theme toggle */}
          <button
            onClick={toggleTheme}
            className="p-2.5 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-slate-500 dark:text-slate-400"
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? <SunIcon className="h-5 w-5" /> : <MoonIcon className="h-5 w-5" />}
          </button>

          {/* Alert bell */}
          <button
            onClick={() => router.push("/alerts")}
            className="relative p-2.5 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            aria-label={`Alerts${activeAlerts.length > 0 ? ` (${activeAlerts.length} active)` : ''}`}
          >
            <BellIcon className="h-5 w-5 text-slate-500 dark:text-slate-400" />
            {activeAlerts.length > 0 && (
              <span className="absolute top-1.5 right-1.5 flex h-4 min-w-[1rem] items-center justify-center rounded-full bg-red-500 px-1 text-[0.625rem] font-bold text-white ring-2 ring-white animate-pulse-ring">
                {activeAlerts.length > 9 ? "9+" : activeAlerts.length}
              </span>
            )}
          </button>

          {/* Divider */}
          {user && <div className="hidden sm:block h-6 w-px bg-slate-200 dark:bg-slate-800 mx-1" />}

          {/* User section */}
          {user && (
            <div className="flex items-center gap-3">
              <div className="hidden xl:block text-right">
                <p className="text-[0.875rem] font-bold text-slate-700 dark:text-slate-200 leading-tight">{user.full_name}</p>
                <p className="text-[0.6875rem] font-semibold text-slate-400 uppercase tracking-widest">{user.role}</p>
              </div>
              <button
                onClick={handleLogout}
                className="flex items-center justify-center h-10 w-10 rounded-full bg-slate-100 dark:bg-white/[0.08] text-slate-600 dark:text-slate-300 hover:bg-red-50 hover:text-red-500 dark:hover:bg-red-500/20 dark:hover:text-red-400 transition-colors"
                title="Logout"
              >
                <ArrowRightOnRectangleIcon className="h-[1.125rem] w-[1.125rem] ml-0.5" />
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
