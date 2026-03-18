"use client";

import { useAuthStore, useAlertStore, useThemeStore } from "@/lib/store";
import { useEffect } from "react";
import {
  BellIcon,
  ArrowRightOnRectangleIcon,
  Bars3Icon,
  SunIcon,
  MoonIcon,
} from "@heroicons/react/24/outline";
import { useRouter } from "next/navigation";

export default function Header({ onMenuToggle }) {
  const { user, logout } = useAuthStore();
  const { activeAlerts, fetchActiveAlerts } = useAlertStore();
  const { theme, toggleTheme } = useThemeStore();
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
    <header className="sticky top-0 z-30 flex items-center justify-between h-16 px-6 bg-white/80 dark:bg-surface-900/80 backdrop-blur-lg border-b border-slate-200/60 dark:border-slate-800/60 shadow-[0_1px_2px_rgba(0,0,0,0.04)] dark:shadow-none">
      {/* Left */}
      <div className="flex items-center gap-3">
        {onMenuToggle && (
          <button
            onClick={onMenuToggle}
            className="lg:hidden p-2 -ml-2 rounded-xl hover:bg-slate-100 transition-colors"
            aria-label="Open menu"
          >
            <Bars3Icon className="h-5 w-5 text-slate-500" />
          </button>
        )}
        <div>
          <h1 className="text-base font-semibold text-slate-800 dark:text-slate-100 tracking-tight">
            AI Predictive Maintenance
          </h1>
          {user?.organization_name && (
            <p className="text-2xs text-slate-400 font-medium">
              {user.organization_name}
            </p>
          )}
        </div>
      </div>

      {/* Right */}
      <div className="flex items-center gap-2">
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
          <BellIcon className="h-[1.125rem] w-[1.125rem] text-slate-500" />
          {activeAlerts.length > 0 && (
            <span className="absolute top-1.5 right-1.5 flex h-4 min-w-[1rem] items-center justify-center rounded-full bg-red-500 px-1 text-[0.625rem] font-bold text-white ring-2 ring-white animate-pulse-ring">
              {activeAlerts.length > 9 ? "9+" : activeAlerts.length}
            </span>
          )}
        </button>

        {/* Divider */}
        {user && <div className="h-6 w-px bg-slate-200/80 mx-1" />}

        {/* User section */}
        {user && (
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-50 text-brand-600 text-xs font-bold">
              {user.full_name?.charAt(0)?.toUpperCase() || "U"}
            </div>
            <div className="hidden sm:block text-right">
              <p className="text-[0.8125rem] font-medium text-slate-700 dark:text-slate-200 leading-tight">{user.full_name}</p>
              <p className="text-2xs text-slate-400 dark:text-slate-500 capitalize">{user.role}</p>
            </div>
            <button
              onClick={handleLogout}
              className="p-2 rounded-xl hover:bg-red-50 dark:hover:bg-red-500/10 text-slate-400 hover:text-red-500 transition-colors"
              aria-label="Logout"
            >
              <ArrowRightOnRectangleIcon className="h-[1.125rem] w-[1.125rem]" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
