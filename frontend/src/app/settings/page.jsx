"use client";

import { useEffect, useState } from "react";
import { useAuthStore } from "@/lib/store";

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
    fetch(
      `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/health`
    )
      .then((r) => r.json())
      .then((data) => setSystemInfo(data))
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
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Settings</h1>
        <p className="text-sm text-slate-500 mt-1">
          System configuration and user preferences
        </p>
      </div>

      {/* Profile */}
      <div className="card">
        <h2 className="text-sm font-semibold text-slate-900 mb-4">Profile</h2>
        <dl className="space-y-3 text-sm max-w-md">
          <div className="flex justify-between">
            <dt className="text-slate-500">Name</dt>
            <dd className="font-medium">{user?.full_name || "—"}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-slate-500">Email</dt>
            <dd className="font-medium">{user?.email || "—"}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-slate-500">Role</dt>
            <dd className="font-medium capitalize">{user?.role || "—"}</dd>
          </div>
        </dl>
      </div>

      {/* System Info — live from health endpoint */}
      <div className="card">
        <h2 className="text-sm font-semibold text-slate-900 mb-4">
          System Information
        </h2>
        <dl className="space-y-3 text-sm max-w-md">
          <div className="flex justify-between">
            <dt className="text-slate-500">Platform Version</dt>
            <dd className="font-medium">
              {systemInfo?.version || "1.0.0"}
            </dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-slate-500">Backend</dt>
            <dd className="font-medium">
              {systemInfo ? `FastAPI + Python (${systemInfo.environment || "unknown"})` : "FastAPI + Python 3.11"}
            </dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-slate-500">ML Framework</dt>
            <dd className="font-medium">PyTorch + XGBoost + LightGBM</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-slate-500">GPU</dt>
            <dd className="font-medium">
              {systemInfo?.gpu || "NVIDIA RTX 3050 6GB (CUDA 12.1)"}
            </dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-slate-500">Database</dt>
            <dd className="font-medium">
              {systemInfo?.database === "connected"
                ? "PostgreSQL — Connected"
                : systemInfo?.database === "disconnected"
                ? "PostgreSQL — Disconnected"
                : "PostgreSQL"}
            </dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-slate-500">Organization</dt>
            <dd className="font-medium">Zydus Pharma Oncology Pvt. Ltd.</dd>
          </div>
        </dl>
      </div>

      {/* Notification Preferences — persisted to localStorage */}
      <div className="card">
        <h2 className="text-sm font-semibold text-slate-900 mb-4">
          Notification Preferences
        </h2>
        <div className="space-y-3 max-w-md">
          {PREF_KEYS.map((key) => (
            <label key={key} className="flex items-center gap-3 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={!!prefs[key]}
                onChange={() => togglePref(key)}
                className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-slate-700">{PREF_LABELS[key]}</span>
            </label>
          ))}
        </div>
      </div>
    </div>
  );
}
