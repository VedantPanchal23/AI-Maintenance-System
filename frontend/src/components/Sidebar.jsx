"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
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
  { name: "Dashboard", href: "/dashboard", icon: HomeIcon },
  { name: "Equipment", href: "/equipment", icon: CpuChipIcon },
  { name: "Alerts", href: "/alerts", icon: BellAlertIcon },
  { name: "Analytics", href: "/analytics", icon: ChartBarIcon },
  { name: "Maintenance", href: "/maintenance", icon: WrenchScrewdriverIcon },
  { name: "ML Models", href: "/ml-admin", icon: BeakerIcon },
  { name: "Settings", href: "/settings", icon: CogIcon },
];

export default function Sidebar({ mobileOpen, onClose }) {
  const pathname = usePathname();

  const sidebarContent = (
    <>
      {/* Brand */}
      <div className="flex items-center justify-between px-6 py-5 border-b border-slate-700/50">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600">
            <CpuChipIcon className="h-5 w-5 text-white" />
          </div>
          <div>
            <p className="text-sm font-bold leading-tight">Predictive</p>
            <p className="text-xs text-slate-400">Maintenance AI</p>
          </div>
        </div>
        {/* Close button — only visible on mobile */}
        {onClose && (
          <button onClick={onClose} className="lg:hidden p-1 rounded hover:bg-slate-800">
            <XMarkIcon className="h-5 w-5 text-slate-400" />
          </button>
        )}
      </div>

      {/* Nav links */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navigation.map((item) => {
          const active = pathname.startsWith(item.href);
          return (
            <Link
              key={item.name}
              href={item.href}
              onClick={onClose}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                active
                  ? "bg-blue-600 text-white"
                  : "text-slate-300 hover:bg-slate-800 hover:text-white"
              )}
            >
              <item.icon className="h-5 w-5 shrink-0" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-slate-700/50">
        <p className="text-xs text-slate-500 text-center">
          Zydus Pharma Oncology
        </p>
        <p className="text-xs text-slate-600 text-center mt-0.5">
          v1.0.0
        </p>
      </div>
    </>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex lg:flex-col lg:w-64 bg-slate-900 text-white">
        {sidebarContent}
      </aside>

      {/* Mobile overlay sidebar */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          {/* Backdrop */}
          <div className="fixed inset-0 bg-black/50" onClick={onClose} />
          {/* Panel */}
          <aside className="fixed inset-y-0 left-0 flex flex-col w-64 bg-slate-900 text-white shadow-xl animate-slide-in">
            {sidebarContent}
          </aside>
        </div>
      )}
    </>
  );
}
