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

const PIE_COLORS = ["#22c55e", "#eab308", "#f97316", "#ef4444", "#6b7280"];

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

    // Real-time WebSocket
    const ws = createSensorWebSocket((data) => {
      setSensorData((prev) => {
        const next = [...prev, data].slice(-100);
        return next;
      });
    });

    // Dashboard re-fetches on its own interval; Header also polls
    // activeAlerts every 30s. To avoid duplicates when dashboard is
    // visible, we only poll the dashboard summary here — Header
    // handles activeAlerts globally.
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
          color: "text-blue-600",
          bg: "bg-blue-50",
        },
        {
          label: "Active Alerts",
          value: summary.active_alerts || 0,
          icon: ExclamationTriangleIcon,
          color: "text-red-600",
          bg: "bg-red-50",
        },
        {
          label: "Healthy Equipment",
          value: summary.healthy_equipment || 0,
          icon: CheckCircleIcon,
          color: "text-green-600",
          bg: "bg-green-50",
        },
        {
          label: "Avg Risk Score",
          value: summary.avg_risk_score
            ? `${(summary.avg_risk_score * 100).toFixed(1)}%`
            : "N/A",
          icon: ArrowTrendingUpIcon,
          color: "text-orange-600",
          bg: "bg-orange-50",
        },
      ]
    : [];

  // Equipment status distribution for pie chart
  const statusDist = summary?.equipment_by_status
    ? Object.entries(summary.equipment_by_status).map(([name, value]) => ({
        name,
        value,
      }))
    : [];

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
        <p className="text-sm text-slate-500 mt-1">
          Real-time overview of equipment health and predictive analytics
        </p>
      </div>

      {/* ─────── Error Banner ─────── */}
      {error && (
        <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700">
          Failed to load dashboard data. Retrying…
        </div>
      )}

      {/* ─────── Stat Cards ─────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.length
          ? stats.map((stat) => (
              <div key={stat.label} className="stat-card">
                <div className="flex items-center justify-between">
                  <span className="stat-label">{stat.label}</span>
                  <div className={`p-2 rounded-lg ${stat.bg}`}>
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

      {/* ─────── Charts Row ─────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk trend chart */}
        <div className="card lg:col-span-2">
          <h2 className="text-sm font-semibold text-slate-900 mb-4">
            Risk Score Trends (7 days)
          </h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={riskTrends}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="#94a3b8" />
              <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" />
              <Tooltip />
              <Bar dataKey="avg_risk" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              <Bar dataKey="max_risk" fill="#ef4444" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Status distribution pie */}
        <div className="card">
          <h2 className="text-sm font-semibold text-slate-900 mb-4">
            Equipment Status
          </h2>
          {statusDist.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={statusDist}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={4}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {statusDist.map((entry, idx) => (
                    <Cell
                      key={entry.name}
                      fill={PIE_COLORS[idx % PIE_COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[220px] text-sm text-slate-400">
              No data
            </div>
          )}
        </div>
      </div>

      {/* ─────── Live sensor feed ─────── */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <BoltIcon className="h-5 w-5 text-cyan-500" />
          <h2 className="text-sm font-semibold text-slate-900">
            Live Sensor Feed
          </h2>
          <span className="badge bg-green-100 text-green-700 ml-auto text-[10px]">
            ● LIVE
          </span>
        </div>
        <SensorChart
          data={sensorData}
          sensors={["air_temperature", "process_temperature", "rotational_speed"]}
          height={280}
        />
      </div>

      {/* ─────── Recent Alerts ─────── */}
      <div>
        <h2 className="text-lg font-semibold text-slate-900 mb-4">
          Active Alerts ({activeAlerts.length})
        </h2>
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
          <div className="card text-center py-8">
            <CheckCircleIcon className="h-10 w-10 text-green-400 mx-auto mb-2" />
            <p className="text-sm text-slate-500">
              No active alerts — all equipment is running normally
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
