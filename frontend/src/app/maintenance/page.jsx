"use client";

import { useEffect, useState } from "react";
import { equipmentAPI } from "@/lib/api";
import { PageSpinner } from "@/components/Loading";
import { formatDate } from "@/lib/utils";
import { StatusBadge } from "@/components/StatusBadge";
import { WrenchScrewdriverIcon, PlusIcon, XMarkIcon } from "@heroicons/react/24/outline";
import KanbanBoard from "./KanbanBoard";

export default function MaintenancePage() {
  const [equipment, setEquipment] = useState([]);
  const [allEquipment, setAllEquipment] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [selectedId, setSelectedId] = useState("");
  const [scheduleLoading, setScheduleLoading] = useState(false);
  const [scheduleError, setScheduleError] = useState("");
  const [fetchError, setFetchError] = useState(null);

  useEffect(() => {
    equipmentAPI
      .list({ status: "maintenance", page_size: 100 })
      .then(({ data }) => setEquipment(data.items || data || []))
      .catch((err) => setFetchError(err.message || "Failed to load maintenance data"))
      .finally(() => setLoading(false));
    equipmentAPI
      .list({ page_size: 100 })
      .then(({ data }) => setAllEquipment(data.items || data || []))
      .catch(console.error);
  }, []);

  if (loading) return <PageSpinner />;
  if (fetchError) {
    return (
      <div className="card empty-state py-16">
        <WrenchScrewdriverIcon className="h-10 w-10 text-red-300 mx-auto mb-3" />
        <p className="font-medium text-slate-500">{fetchError}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">Maintenance Console</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Track and schedule hardware maintenance activities
          </p>
        </div>
        <button onClick={() => setShowModal(true)} className="btn-primary shrink-0">
          <PlusIcon className="h-4 w-4" />
          Schedule Maintenance
        </button>
      </div>

      {/* Maintenance queue */}
      <div className="card">
        <h2 className="section-title mb-6">Equipment Under Maintenance</h2>
        {equipment.length > 0 ? (
          <div className="overflow-x-auto -mx-5">
            <table className="w-full text-sm min-w-[640px]">
              <thead>
                <tr>
                  <th className="table-header pl-5">Equipment</th>
                  <th className="table-header">Type</th>
                  <th className="table-header">Location</th>
                  <th className="table-header">Status</th>
                  <th className="table-header pr-5">Last Maintenance</th>
                </tr>
              </thead>
              <tbody>
                {equipment.map((eq) => (
                  <tr key={eq.id} className="table-row">
                    <td className="table-cell pl-5">
                      <div className="flex items-center gap-2.5">
                        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-50">
                          <WrenchScrewdriverIcon className="h-3.5 w-3.5 text-brand-500" />
                        </div>
                        <span className="font-medium text-slate-700">{eq.name}</span>
                      </div>
                    </td>
                    <td className="table-cell capitalize text-slate-600">
                      {eq.equipment_type?.replace(/_/g, " ")}
                    </td>
                    <td className="table-cell text-slate-500">{eq.location || "—"}</td>
                    <td className="table-cell"><StatusBadge status={eq.status} /></td>
                    <td className="table-cell pr-5 text-slate-500">{formatDate(eq.last_maintenance_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state py-10">
            <WrenchScrewdriverIcon className="h-10 w-10 text-slate-300 mx-auto mb-3" />
            <p className="text-sm font-medium text-slate-500">No equipment under maintenance</p>
            <p className="text-2xs text-slate-400 mt-1">Schedule maintenance for equipment that needs attention</p>
          </div>
        )}
      </div>

      {/* Kanban Board */}
      <div className="mt-8">
        <KanbanBoard />
      </div>

      {/* ─── Schedule Maintenance Modal ─── */}
      {showModal && (
        <div className="modal-overlay" onClick={() => { setShowModal(false); setScheduleError(""); }}>
          <div className="modal-panel w-full max-w-md mx-4" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-semibold text-slate-800">Schedule Maintenance</h2>
              <button onClick={() => { setShowModal(false); setScheduleError(""); }} className="p-1.5 hover:bg-slate-100 rounded-lg transition-colors">
                <XMarkIcon className="h-5 w-5 text-slate-400" />
              </button>
            </div>
            {scheduleError && (
              <div className="mb-4 p-3 rounded-xl bg-red-50 text-sm text-red-600 border border-red-200/60 font-medium">{scheduleError}</div>
            )}
            <form onSubmit={async (e) => {
              e.preventDefault();
              if (!selectedId) return;
              setScheduleLoading(true);
              setScheduleError("");
              try {
                await equipmentAPI.update(selectedId, { status: "maintenance" });
                const { data } = await equipmentAPI.list({ status: "maintenance" });
                setEquipment(data.items || data || []);
                setShowModal(false);
                setSelectedId("");
              } catch (err) {
                setScheduleError(err.response?.data?.detail || "Failed to schedule maintenance");
              } finally {
                setScheduleLoading(false);
              }
            }} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Equipment</label>
                <select value={selectedId} onChange={(e) => setSelectedId(e.target.value)} className="input-field" required>
                  <option value="">Select equipment…</option>
                  {allEquipment.filter(eq => eq.status !== "maintenance").map(eq => (
                    <option key={eq.id} value={eq.id}>{eq.name} ({eq.equipment_type?.replace(/_/g, " ")})</option>
                  ))}
                </select>
              </div>
              <button type="submit" disabled={scheduleLoading || !selectedId} className="btn-primary w-full mt-2">
                {scheduleLoading ? "Scheduling…" : "Schedule Maintenance"}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
