"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Command } from "cmdk";
import { useThemeStore, useAuthStore, useAlertStore } from "@/lib/store";
import {
  HomeIcon,
  CpuChipIcon,
  BellAlertIcon,
  ChartBarIcon,
  WrenchScrewdriverIcon,
  BeakerIcon,
  CogIcon,
  SunIcon,
  MoonIcon,
  ArrowRightOnRectangleIcon,
  ExclamationTriangleIcon
} from "@heroicons/react/24/outline";

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const router = useRouter();
  const { theme, toggleTheme } = useThemeStore();
  const { user, logout } = useAuthStore();
  const { activeAlerts } = useAlertStore();

  useEffect(() => {
    const down = (e) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
    };
    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  const runCommand = (command) => {
    setOpen(false);
    command();
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-start justify-center pt-20 pb-4 px-4 sm:px-6">
      <div className="fixed inset-0 bg-slate-900/40 dark:bg-slate-950/60 backdrop-blur-sm transition-opacity" onClick={() => setOpen(false)} />
      
      <Command 
        className="relative flex w-full max-w-2xl flex-col overflow-hidden rounded-2xl bg-white/90 dark:bg-[#0f172a]/90 backdrop-blur-xl border border-slate-200/50 dark:border-white/[0.08] shadow-2xl ring-1 ring-slate-900/5 dark:ring-white/10"
        shouldFilter={true}
      >
        <div className="flex items-center border-b border-slate-200/50 dark:border-white/[0.08] px-4">
          <Command.Input 
            autoFocus 
            placeholder="Type a command or search... (e.g. 'theme', 'alerts')" 
            className="flex h-16 w-full bg-transparent px-2 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none sm:text-lg"
          />
          <kbd className="hidden sm:inline-flex items-center gap-1 rounded border border-slate-200 dark:border-white/[0.08] bg-slate-50 dark:bg-[#020617] px-2 py-0.5 text-xs font-semibold text-slate-500 dark:text-slate-400 shadow-sm">
            ESC
          </kbd>
        </div>

        <Command.List className="max-h-[60vh] overflow-y-auto p-2 scroll-py-2 custom-scrollbar">
          <Command.Empty className="py-14 text-center text-sm font-medium text-slate-500">No results found.</Command.Empty>
          
          <Command.Group heading="Navigation" className="text-[0.6875rem] font-bold tracking-widest uppercase text-slate-400 px-2 py-3">
            {[
              { name: "Command Center Dashboard", href: "/dashboard", icon: HomeIcon, roles: ["viewer", "engineer", "admin"] },
              { name: "Equipment & Asset Registry", href: "/equipment", icon: CpuChipIcon, roles: ["viewer", "engineer", "admin"] },
              { name: "Incident Pipeline (Alerts)", href: "/alerts", icon: BellAlertIcon, roles: ["viewer", "engineer", "admin"] },
              { name: "Intelligence Hub (Analytics)", href: "/analytics", icon: ChartBarIcon, roles: ["viewer", "engineer", "admin"] },
              { name: "Maintenance Console", href: "/maintenance", icon: WrenchScrewdriverIcon, roles: ["engineer", "admin"] },
              { name: "ML Operations & Training", href: "/ml-admin", icon: BeakerIcon, roles: ["engineer", "admin"] },
              { name: "System Configuration", href: "/settings", icon: CogIcon, roles: ["admin"] },
            ].filter(item => !item.roles || item.roles.includes(user?.role)).map((item) => (
              <Command.Item
                key={item.href}
                onSelect={() => runCommand(() => router.push(item.href))}
                className="flex cursor-pointer select-none items-center gap-3 rounded-xl px-3 py-3 text-sm font-semibold text-slate-700 dark:text-slate-200 outline-none aria-selected:bg-brand-600 aria-selected:text-white dark:aria-selected:bg-brand-500 transition-colors group"
                value={item.name}
              >
                <item.icon className="h-5 w-5 text-slate-400 group-aria-selected:text-white transition-colors" />
                {item.name}
              </Command.Item>
            ))}
          </Command.Group>

          <Command.Separator className="h-px w-full bg-slate-100 dark:bg-white/[0.04] my-2" />
          
          {activeAlerts.length > 0 && (
            <>
              <Command.Group heading="Quick Actions" className="text-[0.6875rem] font-bold tracking-widest uppercase text-red-400 px-2 py-3">
                <Command.Item
                  onSelect={() => runCommand(() => router.push("/alerts"))}
                  className="flex cursor-pointer select-none items-center gap-3 rounded-xl px-3 py-3 text-sm font-semibold text-red-600 dark:text-red-400 outline-none aria-selected:bg-red-600 aria-selected:text-white transition-colors group"
                  value="critical alerts resolve"
                >
                  <ExclamationTriangleIcon className="h-5 w-5 text-red-500 group-aria-selected:text-white" />
                  View {activeAlerts.length} Critical Alerts
                </Command.Item>
              </Command.Group>
            </>
          )}

          <Command.Separator className="h-px w-full bg-slate-100 dark:bg-white/[0.04] my-2" />

          <Command.Group heading="System" className="text-[0.6875rem] font-bold tracking-widest uppercase text-slate-400 px-2 py-3">
            <Command.Item
              onSelect={() => runCommand(toggleTheme)}
              className="flex cursor-pointer select-none items-center gap-3 rounded-xl px-3 py-3 text-sm font-semibold text-slate-700 dark:text-slate-200 outline-none aria-selected:bg-slate-800 aria-selected:text-white dark:aria-selected:bg-white/10 transition-colors group"
              value={`Toggle Theme ${theme === 'dark' ? 'Light' : 'Dark'}`}
            >
              {theme === 'dark' ? (
                <SunIcon className="h-5 w-5 text-slate-400 group-aria-selected:text-white transition-colors" />
              ) : (
                <MoonIcon className="h-5 w-5 text-slate-400 group-aria-selected:text-white transition-colors" />
              )}
              Switch to {theme === 'dark' ? 'Light' : 'Dark'} Mode
            </Command.Item>
            <Command.Item
              onSelect={() => runCommand(() => { logout(); router.push("/login"); })}
              className="flex cursor-pointer select-none items-center gap-3 rounded-xl px-3 py-3 text-sm font-semibold text-red-600 dark:text-red-400 outline-none aria-selected:bg-red-500 aria-selected:text-white transition-colors group"
              value="Log out sign out"
            >
              <ArrowRightOnRectangleIcon className="h-5 w-5 text-red-500 group-aria-selected:text-white transition-colors" />
              Sign Out
            </Command.Item>
          </Command.Group>
        </Command.List>
      </Command>
    </div>
  );
}
