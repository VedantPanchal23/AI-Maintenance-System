"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useCallback } from "react";
import { cn } from "@/lib/utils";
import {
  HomeIcon,
  CpuChipIcon,
  BellAlertIcon,
  ChartBarIcon,
  CogIcon,
  WrenchScrewdriverIcon,
  BeakerIcon,
  XMarkIcon,
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

export default function Sidebar({ mobileOpen, onClose }) {
  const pathname = usePathname();

  // Close mobile sidebar on Escape key
  const handleKeyDown = useCallback((e) => {
    if (e.key === "Escape" && mobileOpen && onClose) onClose();
  }, [mobileOpen, onClose]);

  useEffect(() => {
    if (mobileOpen) {
      document.addEventListener("keydown", handleKeyDown);
      return () => document.removeEventListener("keydown", handleKeyDown);
    }
  }, [mobileOpen, handleKeyDown]);

  const sidebarContent = (
    <div className="flex flex-col h-full">
      {/* ── Brand ── */}
      <div className="flex items-center justify-between px-5 h-16 shrink-0">
        <Link href="/dashboard" className="flex items-center gap-3 group">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-500 shadow-glow-blue transition-shadow group-hover:shadow-lg">
            <CpuChipIcon className="h-5 w-5 text-white" />
          </div>
          <div className="leading-tight">
            <p className="text-[0.8125rem] font-bold text-slate-900 dark:text-white tracking-tight">Predictive</p>
            <p className="text-[0.6875rem] text-slate-500 dark:text-slate-400 font-medium">Maintenance AI</p>
          </div>
        </Link>
        {onClose && (
          <button onClick={onClose} className="lg:hidden p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-white/10 transition-colors">
            <XMarkIcon className="h-5 w-5 text-slate-400" />
          </button>
        )}
      </div>

      {/* ── Divider ── */}
      <div className="mx-4 h-px bg-slate-200 dark:bg-white/[0.04]" />

      {/* ── Navigation ── */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {navigation.map((item) => {
          const active = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.name}
              href={item.href}
              onClick={onClose}
              className={cn(
                "group flex items-center gap-3 px-3 py-2.5 rounded-xl text-[0.8125rem] font-bold tracking-wide transition-all duration-300",
                active
                  ? "bg-brand-600 dark:bg-[#0f172a] text-white dark:border dark:border-white/[0.08] shadow-[0_4px_20px_rgba(2,132,199,0.3)] dark:shadow-[inset_0_1px_0_0_rgba(255,255,255,0.02)]"
                  : "text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-white/[0.04] hover:text-slate-900 dark:hover:text-slate-200"
              )}
            >
              <item.icon className={cn(
                "h-[1.125rem] w-[1.125rem] shrink-0 transition-colors",
                active ? "text-white" : "text-slate-400 group-hover:text-brand-500 dark:group-hover:text-brand-400"
              )} />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* ── Footer ── */}
      <div className="px-4 py-4 mt-auto">
        <div className="rounded-xl bg-slate-100 dark:bg-white/[0.04] px-3 py-3">
          <p className="text-2xs text-slate-500 dark:text-slate-400 text-center font-medium">
            Predictive Maintenance AI
          </p>
          <p className="text-2xs text-slate-400 dark:text-slate-600 text-center mt-0.5">
            v1.0.0
          </p>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Sidebar acts purely as a mobile overlay drawer now */}

      {/* Mobile overlay sidebar */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="fixed inset-0 bg-slate-900/40 dark:bg-slate-950/60 backdrop-blur-sm transition-opacity" onClick={onClose} aria-hidden="true" />
          <aside className="fixed inset-y-0 left-0 flex flex-col w-64 bg-slate-50 dark:bg-[#020617] text-slate-900 dark:text-white shadow-2xl animate-slide-in border-r border-slate-200/60 dark:border-white/[0.04]" role="dialog" aria-modal="true" aria-label="Navigation menu">
            {sidebarContent}
          </aside>
        </div>
      )}
    </>
  );
}
