"use client";

import { useEffect, useState, useMemo } from "react";
import { useDashboardStore, useAlertStore } from "@/lib/store";
import { createSensorWebSocket } from "@/lib/api";
import SensorChart from "@/components/SensorChart";
import AlertCard from "@/components/AlertCard";
import ChartTooltip from "@/components/ChartTooltip";
import { PageSpinner, StatSkeleton } from "@/components/Loading";
import {
  CpuChipIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ArrowTrendingUpIcon,
  BoltIcon,
} from "@heroicons/react/24/outline";
import {
  AreaChart,
  Area,
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
      if (msg?.type === "prediction") {
        // If a failure is predicted, immediately refresh alerts and dashboard stats
        if (msg.predicted_failure) {
          fetchActiveAlerts();
          fetchDashboard();
        }
        return;
      }
      
      // Handle standard sensor readings
      const reading = msg?.type === "sensor_reading" ? msg.data : (msg?.data || msg);
      if (reading && !reading.type) {
        setSensorData((prev) => [...prev, reading].slice(-100));
      }
    });

    const interval = setInterval(() => {
      fetchDashboard();
    }, 10000); // refresh every 10s to sync with auto-prediction cycle

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
            <AreaChart data={riskTrends}>
              <defs>
                <linearGradient id="colorAvg" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.5} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorMax" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#64748b" vertical={false} opacity={0.3} />
              <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <Tooltip content={<ChartTooltip />} />
              <Area type="monotone" dataKey="max_risk" name="Max Risk" stroke="#ef4444" fill="url(#colorMax)" strokeWidth={2} />
              <Area type="monotone" dataKey="avg_risk" name="Avg Risk" stroke="#3b82f6" fill="url(#colorAvg)" strokeWidth={2} />
            </AreaChart>
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
                <Tooltip content={<ChartTooltip />} />
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
