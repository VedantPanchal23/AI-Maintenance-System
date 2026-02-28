"use client";

import { useEffect, useState } from "react";
import { useAlertStore } from "@/lib/store";
import AlertCard from "@/components/AlertCard";
import { PageSpinner } from "@/components/Loading";
import { FunnelIcon, XMarkIcon, BellSlashIcon } from "@heroicons/react/24/outline";

export default function AlertsPage() {
  const {
    alerts,
    loading,
    fetchAlerts,
    acknowledgeAlert,
    resolveAlert,
  } = useAlertStore();

  const [severityFilter, setSeverityFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [resolveTarget, setResolveTarget] = useState(null);
  const [resolveNotes, setResolveNotes] = useState("");
  const [resolveLoading, setResolveLoading] = useState(false);

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  const filtered = alerts.filter((a) => {
    if (severityFilter !== "all" && a.severity !== severityFilter) return false;
    if (statusFilter !== "all" && a.status !== statusFilter) return false;
    return true;
  });

  const handleResolve = (id) => {
    setResolveTarget(id);
    setResolveNotes("");
  };

  const confirmResolve = async () => {
    setResolveLoading(true);
    try {
      await resolveAlert(resolveTarget, resolveNotes || "Resolved from alerts page");
      setResolveTarget(null);
    } catch { /* store already logs */ }
    setResolveLoading(false);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="page-title">Alerts</h1>
        <p className="page-subtitle">
          Equipment failure alerts and maintenance notifications
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <FunnelIcon className="h-4 w-4 text-slate-400" />
        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="input-field w-auto"
        >
          <option value="all">All Severity</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="input-field w-auto"
        >
          <option value="all">All Status</option>
          <option value="active">Active</option>
          <option value="acknowledged">Acknowledged</option>
          <option value="resolved">Resolved</option>
        </select>
        <span className="text-2xs text-slate-400 font-medium ml-auto">
          {filtered.length} alert{filtered.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Alert list */}
      {loading ? (
        <PageSpinner />
      ) : filtered.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {filtered.map((alert) => (
            <AlertCard
              key={alert.id}
              alert={alert}
              onAcknowledge={acknowledgeAlert}
              onResolve={handleResolve}
            />
          ))}
        </div>
      ) : (
        <div className="card empty-state py-14">
          <BellSlashIcon className="h-10 w-10 text-slate-300 mx-auto mb-3" />
          <p className="text-sm font-medium text-slate-500">
            {severityFilter !== "all" || statusFilter !== "all"
              ? "No alerts matching your filters"
              : "No alerts found"}
          </p>
          <p className="text-2xs text-slate-400 mt-1">Alerts will appear here when equipment anomalies are detected</p>
        </div>
      )}

      {/* ─── Resolve Modal ─── */}
      {resolveTarget && (
        <div className="modal-overlay" onClick={() => setResolveTarget(null)}>
          <div className="modal-panel w-full max-w-md mx-4" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-semibold text-slate-800">Resolve Alert</h2>
              <button onClick={() => setResolveTarget(null)} className="p-1.5 hover:bg-slate-100 rounded-lg transition-colors">
                <XMarkIcon className="h-5 w-5 text-slate-400" />
              </button>
            </div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Resolution Notes (optional)</label>
            <textarea
              value={resolveNotes}
              onChange={(e) => setResolveNotes(e.target.value)}
              rows={3}
              className="input-field w-full"
              placeholder="Describe what was done…"
            />
            <div className="flex justify-end gap-2 mt-5">
              <button onClick={() => setResolveTarget(null)} className="btn-ghost text-sm py-2 px-4">Cancel</button>
              <button onClick={confirmResolve} disabled={resolveLoading} className="btn-primary text-sm py-2 px-4">
                {resolveLoading ? "Resolving…" : "Resolve"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
