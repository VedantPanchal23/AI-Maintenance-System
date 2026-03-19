"use client";

import { useEffect, useState } from "react";
import { useAuthStore } from "@/lib/store";
import { analyticsAPI, userAPI } from "@/lib/api";
import {
  UserCircleIcon,
  ServerStackIcon,
  BellIcon,
  UsersIcon
} from "@heroicons/react/24/outline";

const PREF_KEYS = [
  "critical_failure_alerts",
  "high_risk_warnings",
  "maintenance_reminders",
  "model_training_completion",
];

const PREF_LABELS = {
  critical_failure_alerts: "Critical failure alerts",
  high_risk_warnings: "High risk warnings",
  maintenance_reminders: "Maintenance reminders",
  model_training_completion: "Model training completion",
};

function loadPrefs() {
  if (typeof window === "undefined") return {};
  try {
    return JSON.parse(localStorage.getItem("notification_prefs") || "{}");
  } catch {
    return {};
  }
}

function savePrefs(prefs) {
  if (typeof window === "undefined") return;
  localStorage.setItem("notification_prefs", JSON.stringify(prefs));
}

export default function SettingsPage() {
  const user = useAuthStore((s) => s.user);
  const [prefs, setPrefs] = useState({});
  const [systemInfo, setSystemInfo] = useState(null);
  const [users, setUsers] = useState([]);

  useEffect(() => {
    if (user?.role === "admin") {
      userAPI.list().then(({ data }) => setUsers(data)).catch(() => {});
    }
  }, [user?.role]);

  const toggleUserStatus = async (id, isActive) => {
    try {
      await userAPI.updateStatus(id, !isActive);
      setUsers(users.map((u) => (u.id === id ? { ...u, is_active: !isActive } : u)));
    } catch {}
  };

  const changeUserRole = async (id, role) => {
    try {
      await userAPI.updateRole(id, role);
      setUsers(users.map((u) => (u.id === id ? { ...u, role } : u)));
    } catch {}
  };

  // Load persisted prefs on mount
  useEffect(() => {
    const stored = loadPrefs();
    const merged = {};
    PREF_KEYS.forEach((k) => {
      merged[k] = stored[k] !== undefined ? stored[k] : true;
    });
    setPrefs(merged);
  }, []);

  // Fetch live system info from /health
  useEffect(() => {
    analyticsAPI.systemHealth()
      .then(({ data }) => setSystemInfo(data))
      .catch(() => {});
  }, []);

  const togglePref = (key) => {
    setPrefs((prev) => {
      const next = { ...prev, [key]: !prev[key] };
      savePrefs(next);
      return next;
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="page-title">Settings</h1>
        <p className="page-subtitle">
          System configuration and user preferences
        </p>
      </div>

      {/* Profile */}
      <div className="card">
        <div className="flex items-center gap-2 mb-5">
          <UserCircleIcon className="h-5 w-5 text-brand-500" />
          <h2 className="section-title">Profile</h2>
        </div>
        <dl className="space-y-3.5 text-sm max-w-md">
          {[["Name", user?.full_name], ["Email", user?.email], ["Role", user?.role]].map(([label, value]) => (
            <div key={label} className="flex justify-between items-center">
              <dt className="text-slate-400">{label}</dt>
              <dd className="font-medium text-slate-700 capitalize">{value || "—"}</dd>
            </div>
          ))}
        </dl>
      </div>

      {/* System Info */}
      <div className="card">
        <div className="flex items-center gap-2 mb-5">
          <ServerStackIcon className="h-5 w-5 text-slate-500" />
          <h2 className="section-title">System Information</h2>
        </div>
        <dl className="space-y-3.5 text-sm max-w-md">
          {[
            ["Platform Version", systemInfo?.version || "1.0.0"],
            ["Backend", systemInfo ? `FastAPI + Python (${systemInfo.environment || "unknown"})` : "—"],
            ["ML Framework", "PyTorch + XGBoost + LightGBM"],
            ["GPU", systemInfo?.gpu || "—"],
            ["Database", systemInfo?.database === "connected" ? "PostgreSQL — Connected" : systemInfo?.database === "disconnected" ? "PostgreSQL — Disconnected" : "PostgreSQL"],
            ["Organization", user?.organization_name || "—"],
          ].map(([label, value]) => (
            <div key={label} className="flex justify-between items-center">
              <dt className="text-slate-400">{label}</dt>
              <dd className="font-medium text-slate-700">{value}</dd>
            </div>
          ))}
        </dl>
      </div>

      {/* Notification Preferences */}
      <div className="card">
        <div className="flex items-center gap-2 mb-5">
          <BellIcon className="h-5 w-5 text-amber-500" />
          <h2 className="section-title">Notification Preferences</h2>
        </div>
        <div className="space-y-3 max-w-md">
          {PREF_KEYS.map((key) => (
            <label
              key={key}
              className="flex items-center justify-between py-2 px-3 -mx-3 rounded-xl hover:bg-slate-50 cursor-pointer transition-colors"
            >
              <span className="text-sm text-slate-600">{PREF_LABELS[key]}</span>
              <button
                type="button"
                role="switch"
                aria-checked={!!prefs[key]}
                onClick={() => togglePref(key)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200 ${
                  prefs[key] ? "bg-brand-600" : "bg-slate-200"
                }`}
              >
                <span
                  className={`inline-block h-[18px] w-[18px] transform rounded-full bg-white shadow-sm transition-transform duration-200 ${
                    prefs[key] ? "translate-x-[22px]" : "translate-x-[3px]"
                  }`}
                />
              </button>
            </label>
          ))}
        </div>
      </div>

      {/* User Management (Admin Only) */}
      {user?.role === "admin" && (
        <div className="card">
          <div className="flex items-center gap-2 mb-5">
            <UsersIcon className="h-5 w-5 text-indigo-500" />
            <h2 className="section-title">Directory Management</h2>
          </div>
          <div className="overflow-x-auto -mx-5 px-5">
            <table className="w-full text-sm min-w-[600px]">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-700/50">
                  <th className="pb-3 text-left font-semibold text-slate-500">User</th>
                  <th className="pb-3 text-left font-semibold text-slate-500">Email</th>
                  <th className="pb-3 text-left font-semibold text-slate-500">Role</th>
                  <th className="pb-3 text-right font-semibold text-slate-500">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/50">
                {users.map((u) => (
                  <tr key={u.id}>
                    <td className="py-3 font-medium text-slate-900 dark:text-white capitalize">{u.full_name}</td>
                    <td className="py-3 text-slate-500">{u.email}</td>
                    <td className="py-3">
                      <select
                        value={u.role}
                        onChange={(e) => changeUserRole(u.id, e.target.value)}
                        disabled={u.id === user?.id}
                        className="bg-slate-50 dark:bg-surface-800 text-slate-700 dark:text-slate-300 text-xs rounded-lg px-2 py-1 outline-none border border-slate-200 dark:border-slate-700 focus:border-brand-500"
                      >
                        <option value="viewer">Viewer</option>
                        <option value="engineer">Engineer</option>
                        <option value="admin">Admin</option>
                      </select>
                    </td>
                    <td className="py-3 text-right">
                      <button
                        onClick={() => toggleUserStatus(u.id, u.is_active)}
                        disabled={u.id === user?.id}
                        className={`text-xs font-semibold px-2 py-1 rounded-lg ${
                          u.is_active ? "bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-400" : "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400"
                        } disabled:opacity-50 transition-colors`}
                      >
                        {u.is_active ? "Active" : "Suspended"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
