"use client";

import { useEffect, useState } from "react";
import { useDashboardStore, useAlertStore } from "@/lib/store";
import { createSensorWebSocket } from "@/lib/api";
import SensorChart from "@/components/SensorChart";
import AlertCard from "@/components/AlertCard";
import { StatusBadge } from "@/components/StatusBadge";
import { PageSpinner, StatSkeleton } from "@/components/Loading";
import {
  CpuChipIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ArrowTrendingUpIcon,
  BoltIcon,
} from "@heroicons/react/24/outline";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

const PIE_COLORS = ["#22c55e", "#eab308", "#f97316", "#ef4444", "#94a3b8"];

export default function DashboardPage() {
  const { summary, loading, error, fetchDashboard, fetchRiskTrends, riskTrends } =
    useDashboardStore();
  const { activeAlerts, fetchActiveAlerts, acknowledgeAlert, resolveAlert } =
    useAlertStore();
  const [sensorData, setSensorData] = useState([]);

  useEffect(() => {
    fetchDashboard();
    fetchRiskTrends(7);
    fetchActiveAlerts();

    const ws = createSensorWebSocket((msg) => {
      const reading = msg?.data || msg;
      setSensorData((prev) => [...prev, reading].slice(-100));
    });

    const interval = setInterval(() => {
      fetchDashboard();
    }, 30000);

    return () => {
      ws.close();
      clearInterval(interval);
    };
  }, [fetchDashboard, fetchRiskTrends, fetchActiveAlerts]);

  if (loading && !summary) return <PageSpinner />;

  const stats = summary
    ? [
        {
          label: "Total Equipment",
          value: summary.total_equipment || 0,
          icon: CpuChipIcon,
          color: "text-brand-600",
          bg: "bg-brand-50",
        },
        {
          label: "Active Alerts",
          value: summary.active_alerts || 0,
          icon: ExclamationTriangleIcon,
          color: "text-red-500",
          bg: "bg-red-50",
        },
        {
          label: "Healthy Equipment",
          value: summary.healthy_equipment || 0,
          icon: CheckCircleIcon,
          color: "text-emerald-500",
          bg: "bg-emerald-50",
        },
        {
          label: "Avg Risk Score",
          value: summary.avg_risk_score
            ? `${(summary.avg_risk_score * 100).toFixed(1)}%`
            : "N/A",
          icon: ArrowTrendingUpIcon,
          color: "text-amber-500",
          bg: "bg-amber-50",
        },
      ]
    : [];

  const statusDist = summary?.equipment_by_status
    ? Object.entries(summary.equipment_by_status).map(([name, value]) => ({
        name,
        value,
      }))
    : [];

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    return (
      <div className="rounded-xl bg-white px-3 py-2 shadow-elevated border border-slate-100 text-xs">
        <p className="font-medium text-slate-700 mb-1">{label}</p>
        {payload.map((p) => (
          <p key={p.dataKey} className="text-slate-500">
            <span className="inline-block w-2 h-2 rounded-full mr-1.5" style={{ background: p.fill || p.color }} />
            {p.name || p.dataKey}: <span className="font-semibold text-slate-700">{typeof p.value === 'number' ? p.value.toFixed(2) : p.value}</span>
          </p>
        ))}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">
          Real-time overview of equipment health and predictive analytics
        </p>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="flex items-center gap-2 p-3.5 rounded-xl bg-red-50 border border-red-200/60 text-sm text-red-600 font-medium">
          <ExclamationTriangleIcon className="h-4 w-4 shrink-0" />
          Failed to load dashboard data. Retrying…
        </div>
      )}

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.length
          ? stats.map((stat) => (
              <div key={stat.label} className="stat-card group">
                <div className="flex items-center justify-between mb-3">
                  <span className="stat-label">{stat.label}</span>
                  <div className={`p-2 rounded-xl ${stat.bg} transition-transform group-hover:scale-110`}>
                    <stat.icon className={`h-5 w-5 ${stat.color}`} />
                  </div>
                </div>
                <span className="stat-value">{stat.value}</span>
              </div>
            ))
          : Array(4)
              .fill(0)
              .map((_, i) => <StatSkeleton key={i} />)}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Risk trend chart */}
        <div className="card lg:col-span-2">
          <h2 className="section-title mb-4">Risk Score Trends (7 days)</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={riskTrends} barGap={2}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="#94a3b8" axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="avg_risk" name="Avg Risk" fill="#3b82f6" radius={[6, 6, 0, 0]} />
              <Bar dataKey="max_risk" name="Max Risk" fill="#ef4444" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Status distribution pie */}
        <div className="card">
          <h2 className="section-title mb-4">Equipment Status</h2>
          {statusDist.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={statusDist}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={82}
                  paddingAngle={3}
                  dataKey="value"
                  strokeWidth={0}
                >
                  {statusDist.map((entry, idx) => (
                    <Cell
                      key={entry.name}
                      fill={PIE_COLORS[idx % PIE_COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state h-[220px]">
              <p>No status data</p>
            </div>
          )}
          {/* Legend */}
          {statusDist.length > 0 && (
            <div className="flex flex-wrap justify-center gap-x-4 gap-y-1 mt-2">
              {statusDist.map((entry, idx) => (
                <div key={entry.name} className="flex items-center gap-1.5 text-2xs text-slate-500">
                  <span className="inline-block w-2.5 h-2.5 rounded-full" style={{ background: PIE_COLORS[idx % PIE_COLORS.length] }} />
                  <span className="capitalize">{entry.name}</span>
                  <span className="font-semibold text-slate-700">{entry.value}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Live sensor feed */}
      <div className="card">
        <div className="flex items-center gap-2.5 mb-4">
          <BoltIcon className="h-5 w-5 text-cyan-500" />
          <h2 className="section-title">Live Sensor Feed</h2>
          <span className="badge bg-emerald-50 text-emerald-600 ml-auto">
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse mr-1" />
            LIVE
          </span>
        </div>
        <SensorChart
          data={sensorData}
          sensors={["air_temperature", "process_temperature", "rotational_speed"]}
          height={280}
        />
      </div>

      {/* Recent Alerts */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="section-title text-base">
            Active Alerts
            {activeAlerts.length > 0 && (
              <span className="ml-2 inline-flex items-center justify-center h-5 min-w-[1.25rem] rounded-full bg-red-100 px-1.5 text-2xs font-bold text-red-600">
                {activeAlerts.length}
              </span>
            )}
          </h2>
        </div>
        {activeAlerts.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {activeAlerts.slice(0, 6).map((alert) => (
              <AlertCard
                key={alert.id}
                alert={alert}
                onAcknowledge={acknowledgeAlert}
                onResolve={(id) => resolveAlert(id, "Resolved from dashboard")}
              />
            ))}
          </div>
        ) : (
          <div className="card empty-state py-10">
            <CheckCircleIcon className="h-10 w-10 text-emerald-300 mx-auto mb-3" />
            <p className="text-sm font-medium text-slate-500">All systems operational</p>
            <p className="text-2xs text-slate-400 mt-1">No active alerts — all equipment is running normally</p>
          </div>
        )}
      </div>
    </div>
  );
}
