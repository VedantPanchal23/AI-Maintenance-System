"use client";

import { useEffect, useState } from "react";
import { useAuthStore } from "@/lib/store";
import { analyticsAPI } from "@/lib/api";
import {
  UserCircleIcon,
  ServerStackIcon,
  BellIcon,
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
    </div>
  );
}
