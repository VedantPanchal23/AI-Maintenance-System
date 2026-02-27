"use client";

import { useAuthStore, useAlertStore } from "@/lib/store";
import { useEffect } from "react";
import { BellIcon, ArrowRightOnRectangleIcon, Bars3Icon } from "@heroicons/react/24/outline";
import { useRouter } from "next/navigation";

export default function Header({ onMenuToggle }) {
  const { user, logout } = useAuthStore();
  const { activeAlerts, fetchActiveAlerts } = useAlertStore();
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
    <header className="flex items-center justify-between h-16 px-6 bg-white border-b border-slate-200">
      {/* Left: hamburger + Page context */}
      <div className="flex items-center gap-3">
        {onMenuToggle && (
          <button
            onClick={onMenuToggle}
            className="lg:hidden p-2 -ml-2 rounded-lg hover:bg-slate-100 transition-colors"
            aria-label="Open menu"
          >
            <Bars3Icon className="h-5 w-5 text-slate-600" />
          </button>
        )}
        <div>
          <h1 className="text-lg font-semibold text-slate-900">
            AI Predictive Maintenance
          </h1>
          <p className="text-xs text-slate-500">
            Zydus Pharma Oncology Pvt. Ltd.
          </p>
        </div>
      </div>

      {/* Right: Alerts + User */}
      <div className="flex items-center gap-4">
        {/* Alert bell */}
        <button
          onClick={() => router.push("/alerts")}
          className="relative p-2 rounded-lg hover:bg-slate-100 transition-colors"
        >
          <BellIcon className="h-5 w-5 text-slate-600" />
          {activeAlerts.length > 0 && (
            <span className="absolute -top-0.5 -right-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
              {activeAlerts.length > 9 ? "9+" : activeAlerts.length}
            </span>
          )}
        </button>

        {/* User info */}
        {user && (
          <div className="flex items-center gap-3 pl-3 border-l border-slate-200">
            <div className="text-right">
              <p className="text-sm font-medium text-slate-900">{user.full_name}</p>
              <p className="text-xs text-slate-500 capitalize">{user.role}</p>
            </div>
            <button
              onClick={handleLogout}
              className="p-2 rounded-lg hover:bg-slate-100 transition-colors"
              title="Logout"
            >
              <ArrowRightOnRectangleIcon className="h-5 w-5 text-slate-500" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
