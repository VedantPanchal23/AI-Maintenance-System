"use client";

import { useEffect, useState } from "react";
import { useDashboardStore, useAlertStore } from "@/lib/store";
import { createSensorWebSocket } from "@/lib/api";
import SensorChart from "@/components/SensorChart";
import ChartTooltip from "@/components/ChartTooltip";
import { PageSpinner, StatSkeleton } from "@/components/Loading";
import { AnimatedNumber } from "@/components/AnimatedNumber";
import { toast } from "sonner";
import {
  CpuChipIcon,
  ExclamationTriangleIcon,
  BoltIcon,
  ShieldCheckIcon,
  ArrowRightIcon,
  CheckCircleIcon
} from "@heroicons/react/24/outline";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import Link from "next/link";
import { timeAgo } from "@/lib/utils";

export default function DashboardPage() {
  const { summary, loading, error, fetchDashboard, fetchRiskTrends, riskTrends } = useDashboardStore();
  const { activeAlerts, fetchActiveAlerts, acknowledgeAlert, resolveAlert } = useAlertStore();
  const [sensorData, setSensorData] = useState([]);

  useEffect(() => {
    fetchDashboard();
    fetchRiskTrends(7);
    fetchActiveAlerts();

    const ws = createSensorWebSocket((msg) => {
      if (msg?.type === "prediction" && msg.predicted_failure) {
        toast.error(`Anomaly Detected: ${msg.equipment_name || 'Asset'}`, {
          description: `Failure probability reached ${(msg.failure_probability * 100).toFixed(0)}%. System requires immediate attention.`
        });
        fetchActiveAlerts();
        fetchDashboard();
        return;
      }
      
      const reading = msg?.type === "sensor_reading" ? msg.data : (msg?.data || msg);
      if (reading && !reading.type) {
        setSensorData((prev) => [...prev, reading].slice(-80));
      }
    });

    const interval = setInterval(() => { fetchDashboard(); }, 10000);
    return () => { ws.close(); clearInterval(interval); };
  }, [fetchDashboard, fetchRiskTrends, fetchActiveAlerts]);

  if (loading && !summary) return <PageSpinner />;

  // Calculate System Health KPI (Inverse of risk)
  const avgRisk = summary?.avg_risk_score || 0;
  const healthScore = Math.max(0, 100 - (avgRisk * 100)).toFixed(1);
  
  // Status Distribution for beautiful progress bars
  const totalEquip = summary?.total_equipment || 1; 
  const statuses = summary?.equipment_by_status || {};
  const operational = statuses.operational || 0;
  const critical = statuses.critical || 0;
  const maintenance = statuses.maintenance || 0;

  return (
    <div className="space-y-8 pb-8">
      {/* ─── HEADER SECTION ─── */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">Command Center</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Real-time multi-asset surveillance and predictive diagnostics
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-200 dark:border-emerald-500/20 text-xs font-semibold text-emerald-700 dark:text-emerald-400 tracking-wide">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            SYSTEM ONLINE
          </span>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-sm text-red-600 font-medium">
          Failed to load dashboard data. Connection disrupted.
        </div>
      )}

      {/* ─── PRIMARY KPIs ─── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 xl:gap-6">
        <div className="card !p-5 flex flex-col justify-between hover:-translate-y-1 transition-transform">
          <div className="flex items-start justify-between">
            <p className="text-xs font-bold text-slate-500 tracking-wider uppercase">System Health</p>
            <ShieldCheckIcon className="h-5 w-5 text-emerald-500" />
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <AnimatedNumber value={parseFloat(healthScore) || 0} format={(v) => v.toFixed(1)} className="text-4xl font-extrabold text-slate-900 dark:text-white tracking-tighter" />
            <span className="text-sm font-medium text-slate-500">/ 100</span>
          </div>
        </div>

        <div className="card !p-5 flex flex-col justify-between hover:-translate-y-1 transition-transform">
          <div className="flex items-start justify-between">
            <p className="text-xs font-bold text-slate-500 tracking-wider uppercase">Active Alerts</p>
            <ExclamationTriangleIcon className={`h-5 w-5 ${activeAlerts.length > 0 ? 'text-red-500' : 'text-slate-400'}`} />
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <AnimatedNumber value={summary?.active_alerts || 0} className="text-4xl font-extrabold text-slate-900 dark:text-white tracking-tighter" />
            <span className="text-sm font-medium text-slate-500">requires attention</span>
          </div>
        </div>

        <div className="card !p-5 flex flex-col justify-between hover:-translate-y-1 transition-transform">
          <div className="flex items-start justify-between">
            <p className="text-xs font-bold text-slate-500 tracking-wider uppercase">Monitored Assets</p>
            <CpuChipIcon className="h-5 w-5 text-brand-500" />
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <AnimatedNumber value={summary?.total_equipment || 0} className="text-4xl font-extrabold text-slate-900 dark:text-white tracking-tighter" />
            <span className="text-sm font-medium text-slate-500">connected nodes</span>
          </div>
        </div>

        <div className="card !p-5 flex flex-col justify-between hover:-translate-y-1 transition-transform">
          <div className="flex items-start justify-between">
            <p className="text-xs font-bold text-slate-500 tracking-wider uppercase">Data Throughput</p>
            <BoltIcon className="h-5 w-5 text-cyan-500" />
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <AnimatedNumber value={60} className="text-4xl font-extrabold text-slate-900 dark:text-white tracking-tighter" />
            <span className="text-sm font-medium text-slate-500">Hz avg</span>
          </div>
        </div>
      </div>

      {/* ─── MAIN GRID ─── */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        
        {/* LEFT COLUMN: Data Streams */}
        <div className="xl:col-span-2 space-y-6">
          
          {/* Live Sensor Feed */}
          <div className="card flex flex-col overflow-hidden">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">Live Telemetry</h2>
              <span className="flex h-5 items-center rounded-full bg-brand-500/10 px-2 text-[0.625rem] font-bold text-brand-600 dark:text-brand-400 uppercase tracking-widest ring-1 ring-inset ring-brand-500/20">LIVE</span>
            </div>
            <div className="-mx-2 mt-auto">
              <SensorChart
                data={sensorData}
                sensors={["air_temperature", "process_temperature", "rotational_speed"]}
                height={280}
              />
            </div>
          </div>

          {/* Risk Horizon */}
          <div className="card">
            <div className="flex items-center justify-between xl:mb-6 mb-4">
              <h2 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">7-Day Risk Horizon</h2>
            </div>
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={riskTrends} margin={{ top: 10, right: 0, left: -25, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorMax" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#ef4444" stopOpacity={0.4} />
                    <stop offset="100%" stopColor="#ef4444" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#64748b" opacity={0.15} />
                <XAxis dataKey="date" tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: '#64748b' }} dy={10} />
                <YAxis tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: '#64748b' }} />
                <Tooltip content={<ChartTooltip />} />
                <Area type="monotone" dataKey="max_risk" stroke="#ef4444" strokeWidth={2} fill="url(#colorMax)" isAnimationActive={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* RIGHT COLUMN: Status & Alerts */}
        <div className="space-y-6">
          
          {/* Fleet Status */}
          <div className="card">
            <h2 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider mb-6">Fleet Status</h2>
            <div className="space-y-5">
              
              {/* Operational Block */}
              <div>
                <div className="flex justify-between text-sm mb-1.5">
                  <span className="font-medium text-slate-700 dark:text-slate-300">Operational</span>
                  <span className="font-bold text-slate-900 dark:text-white">{operational}</span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                  <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${(operational / totalEquip) * 100}%` }} />
                </div>
              </div>

              {/* Maintenance Block */}
              <div>
                <div className="flex justify-between text-sm mb-1.5">
                  <span className="font-medium text-slate-700 dark:text-slate-300">In Maintenance</span>
                  <span className="font-bold text-slate-900 dark:text-white">{maintenance}</span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                  <div className="h-full bg-amber-500 rounded-full" style={{ width: `${(maintenance / totalEquip) * 100}%` }} />
                </div>
              </div>

              {/* Critical Block */}
              <div>
                <div className="flex justify-between text-sm mb-1.5">
                  <span className="font-medium text-slate-700 dark:text-slate-300">Critical Pipeline</span>
                  <span className="font-bold text-slate-900 dark:text-white">{critical}</span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                  <div className="h-full bg-red-500 rounded-full" style={{ width: `${(critical / totalEquip) * 100}%` }} />
                </div>
              </div>

            </div>
          </div>

          {/* Actionable Alerts Feed */}
          <div className="card flex flex-col h-[360px]">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">Incident Pipeline</h2>
              <Link href="/alerts" className="text-xs font-semibold text-brand-600 dark:text-brand-400 hover:underline">
                View All
              </Link>
            </div>
            
            <div className="flex-1 overflow-y-auto pr-2 -mr-2 space-y-3">
              {activeAlerts.length > 0 ? (
                activeAlerts.slice(0, 5).map(alert => (
                  <div key={alert.id} className="p-3.5 rounded-xl border border-slate-100 dark:border-white/[0.04] bg-slate-50 dark:bg-slate-800/30 hover:bg-white dark:hover:bg-slate-800/60 transition-colors">
                    <div className="flex justify-between items-start gap-2">
                      <div className="min-w-0">
                        <h4 className="text-sm font-semibold text-slate-900 dark:text-white truncate">{alert.title || "Critical Anomaly"}</h4>
                        <p className="text-xs text-slate-500 mt-0.5 truncate">{alert.equipment_name} &middot; {timeAgo(alert.created_at)}</p>
                      </div>
                      <span className="shrink-0 flex items-center justify-center px-2 py-1 rounded-md bg-red-100 dark:bg-red-500/20 text-[10px] font-bold text-red-700 dark:text-red-400 uppercase tracking-widest">
                        {(alert.failure_probability * 100).toFixed(0)}%
                      </span>
                    </div>
                    {alert.status === "active" && (
                      <div className="mt-3 flex gap-2">
                        <button onClick={() => acknowledgeAlert(alert.id)} className="flex-1 py-1.5 px-3 text-xs font-semibold rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 transition-colors">
                          Ack
                        </button>
                        <button onClick={() => resolveAlert(alert.id)} className="flex-1 py-1.5 px-3 text-xs font-semibold rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition-colors">
                          Resolve
                        </button>
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-center px-4 opacity-70">
                  <CheckCircleIcon className="h-12 w-12 text-emerald-500 mb-3" />
                  <p className="text-sm font-semibold text-slate-900 dark:text-white">Zero Incidents</p>
                  <p className="text-xs text-slate-500 mt-1">All monitoring nodes report optimal health.</p>
                </div>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
