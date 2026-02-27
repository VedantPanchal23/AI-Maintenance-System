"use client";

import { useEffect, useState } from "react";
import { useEquipmentStore } from "@/lib/store";
import EquipmentCard from "@/components/EquipmentCard";
import { PageSpinner, CardSkeleton } from "@/components/Loading";
import { PlusIcon, MagnifyingGlassIcon, XMarkIcon } from "@heroicons/react/24/outline";
import { equipmentAPI } from "@/lib/api";

const EQUIPMENT_TYPES = [
  { value: "cnc_mill", label: "CNC Mill" },
  { value: "hydraulic_press", label: "Hydraulic Press" },
  { value: "injection_molder", label: "Injection Molder" },
  { value: "conveyor", label: "Conveyor" },
  { value: "compressor", label: "Compressor" },
  { value: "pump", label: "Pump" },
  { value: "motor", label: "Motor" },
];

export default function EquipmentPage() {
  const { equipment, loading, fetchEquipment } = useEquipmentStore();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [showAddModal, setShowAddModal] = useState(false);
  const [addForm, setAddForm] = useState({ name: "", equipment_type: "cnc_mill", location: "" });
  const [addLoading, setAddLoading] = useState(false);
  const [addError, setAddError] = useState("");

  useEffect(() => {
    fetchEquipment();
  }, [fetchEquipment]);

  const filtered = equipment.filter((eq) => {
    const matchesSearch =
      !search ||
      eq.name?.toLowerCase().includes(search.toLowerCase()) ||
      eq.equipment_type?.toLowerCase().includes(search.toLowerCase()) ||
      eq.location?.toLowerCase().includes(search.toLowerCase());

    const matchesStatus =
      statusFilter === "all" || eq.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Equipment</h1>
          <p className="text-sm text-slate-500 mt-1">
            Monitor and manage all equipment units
          </p>
        </div>
        <button onClick={() => setShowAddModal(true)} className="btn-primary">
          <PlusIcon className="h-4 w-4" />
          Add Equipment
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search equipment..."
            className="input-field pl-9"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="input-field w-auto"
        >
          <option value="all">All Status</option>
          <option value="operational">Operational</option>
          <option value="warning">Warning</option>
          <option value="critical">Critical</option>
          <option value="maintenance">Maintenance</option>
          <option value="offline">Offline</option>
        </select>
      </div>

      {/* Grid */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array(6)
            .fill(0)
            .map((_, i) => (
              <CardSkeleton key={i} />
            ))}
        </div>
      ) : filtered.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((eq) => (
            <EquipmentCard key={eq.id} equipment={eq} />
          ))}
        </div>
      ) : (
        <div className="card text-center py-12">
          <p className="text-sm text-slate-500">
            {search || statusFilter !== "all"
              ? "No equipment matching your filters"
              : "No equipment found. Add your first unit."}
          </p>
        </div>
      )}

      {/* ─── Add Equipment Modal ─── */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-slate-900">Add Equipment</h2>
              <button onClick={() => { setShowAddModal(false); setAddError(""); }} className="p-1 hover:bg-slate-100 rounded">
                <XMarkIcon className="h-5 w-5 text-slate-500" />
              </button>
            </div>
            {addError && <div className="mb-3 p-2 rounded bg-red-50 text-sm text-red-700 border border-red-200">{addError}</div>}
            <form onSubmit={async (e) => {
              e.preventDefault();
              setAddLoading(true);
              setAddError("");
              try {
                await equipmentAPI.create(addForm);
                setShowAddModal(false);
                setAddForm({ name: "", equipment_type: "cnc_mill", location: "" });
                fetchEquipment();
              } catch (err) {
                setAddError(err.response?.data?.detail || "Failed to add equipment");
              } finally {
                setAddLoading(false);
              }
            }} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Name</label>
                <input type="text" required value={addForm.name} onChange={(e) => setAddForm(p => ({ ...p, name: e.target.value }))} className="input-field" placeholder="Equipment name" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Type</label>
                <select value={addForm.equipment_type} onChange={(e) => setAddForm(p => ({ ...p, equipment_type: e.target.value }))} className="input-field">
                  {EQUIPMENT_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Location</label>
                <input type="text" value={addForm.location} onChange={(e) => setAddForm(p => ({ ...p, location: e.target.value }))} className="input-field" placeholder="Optional location" />
              </div>
              <button type="submit" disabled={addLoading} className="btn-primary w-full">
                {addLoading ? "Adding…" : "Add Equipment"}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
