"use client";

import { useEffect, useState } from "react";
import { equipmentAPI } from "@/lib/api";
import { PageSpinner } from "@/components/Loading";
import { formatDate } from "@/lib/utils";
import { StatusBadge } from "@/components/StatusBadge";
import { WrenchScrewdriverIcon, PlusIcon, XMarkIcon } from "@heroicons/react/24/outline";

export default function MaintenancePage() {
  const [equipment, setEquipment] = useState([]);
  const [allEquipment, setAllEquipment] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [selectedId, setSelectedId] = useState("");
  const [scheduleLoading, setScheduleLoading] = useState(false);
  const [scheduleError, setScheduleError] = useState("");

  useEffect(() => {
    equipmentAPI
      .list({ status: "maintenance" })
      .then(({ data }) => setEquipment(data.items || data || []))
      .catch(console.error)
      .finally(() => setLoading(false));
    // Fetch all equipment for the scheduling dropdown
    equipmentAPI
      .list()
      .then(({ data }) => setAllEquipment(data.items || data || []))
      .catch(console.error);
  }, []);

  if (loading) return <PageSpinner />;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Maintenance</h1>
          <p className="text-sm text-slate-500 mt-1">
            Track and schedule maintenance activities
          </p>
        </div>
        <button onClick={() => setShowModal(true)} className="btn-primary">
          <PlusIcon className="h-4 w-4" />
          Schedule Maintenance
        </button>
      </div>

      {/* Maintenance queue */}
      <div className="card">
        <h2 className="text-sm font-semibold text-slate-900 mb-4">
          Equipment Under Maintenance
        </h2>
        {equipment.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="text-left py-2 text-slate-500 font-medium">
                    Equipment
                  </th>
                  <th className="text-left py-2 text-slate-500 font-medium">
                    Type
                  </th>
                  <th className="text-left py-2 text-slate-500 font-medium">
                    Location
                  </th>
                  <th className="text-left py-2 text-slate-500 font-medium">
                    Status
                  </th>
                  <th className="text-left py-2 text-slate-500 font-medium">
                    Last Maintenance
                  </th>
                </tr>
              </thead>
              <tbody>
                {equipment.map((eq) => (
                  <tr
                    key={eq.id}
                    className="border-b border-slate-100 hover:bg-slate-50"
                  >
                    <td className="py-3 flex items-center gap-2">
                      <WrenchScrewdriverIcon className="h-4 w-4 text-blue-500" />
                      <span className="font-medium">{eq.name}</span>
                    </td>
                    <td className="py-3 capitalize">
                      {eq.equipment_type?.replace(/_/g, " ")}
                    </td>
                    <td className="py-3">{eq.location || "—"}</td>
                    <td className="py-3">
                      <StatusBadge status={eq.status} />
                    </td>
                    <td className="py-3">
                      {formatDate(eq.last_maintenance_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8">
            <WrenchScrewdriverIcon className="h-10 w-10 text-slate-300 mx-auto mb-2" />
            <p className="text-sm text-slate-500">
              No equipment currently under maintenance
            </p>
          </div>
        )}
      </div>

      {/* ─── Schedule Maintenance Modal ─── */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-slate-900">Schedule Maintenance</h2>
              <button onClick={() => { setShowModal(false); setScheduleError(""); }} className="p-1 hover:bg-slate-100 rounded">
                <XMarkIcon className="h-5 w-5 text-slate-500" />
              </button>
            </div>
            {scheduleError && <div className="mb-3 p-2 rounded bg-red-50 text-sm text-red-700 border border-red-200">{scheduleError}</div>}
            <form onSubmit={async (e) => {
              e.preventDefault();
              if (!selectedId) return;
              setScheduleLoading(true);
              setScheduleError("");
              try {
                await equipmentAPI.update(selectedId, { status: "maintenance" });
                // Refresh both lists
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
                <label className="block text-sm font-medium text-slate-700 mb-1">Equipment</label>
                <select value={selectedId} onChange={(e) => setSelectedId(e.target.value)} className="input-field" required>
                  <option value="">Select equipment…</option>
                  {allEquipment.filter(eq => eq.status !== "maintenance").map(eq => (
                    <option key={eq.id} value={eq.id}>{eq.name} ({eq.equipment_type?.replace(/_/g, " ")})</option>
                  ))}
                </select>
              </div>
              <button type="submit" disabled={scheduleLoading || !selectedId} className="btn-primary w-full">
                {scheduleLoading ? "Scheduling…" : "Schedule Maintenance"}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
