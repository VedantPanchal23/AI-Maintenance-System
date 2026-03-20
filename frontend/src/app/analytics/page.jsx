"use client";

import { useEffect, useState } from "react";
import { analyticsAPI } from "@/lib/api";
import { PageSpinner } from "@/components/Loading";
import ChartTooltip from "@/components/ChartTooltip";
import {
  ChartBarSquareIcon,
  ExclamationTriangleIcon,
  DocumentArrowDownIcon
} from "@heroicons/react/24/outline";
import { generateExecutiveReport } from "@/lib/export";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  Legend,
} from "recharts";

export default function AnalyticsPage() {
  const [dashboard, setDashboard] = useState(null);
  const [trends, setTrends] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [range, setRange] = useState(7);

  useEffect(() => {
    setLoading(true);
    setError(null);
    async function load() {
      try {
        const [dashRes, trendRes] = await Promise.allSettled([
          analyticsAPI.dashboard(),
          analyticsAPI.riskTrends({ hours: range * 24 }),
        ]);
        if (dashRes.status === "fulfilled") {
          setDashboard(dashRes.value.data);
        } else {
          setError("Failed to load dashboard data");
        }
        if (trendRes.status === "fulfilled") {
          setTrends(trendRes.value.data || []);
        }
      } catch (err) {
        setError("Failed to load analytics data");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [range]);

  if (loading) return <PageSpinner />;

  const healthData = dashboard?.equipment_health || [];

  const ranges = [7, 14, 30, 90];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">Intelligence Hub</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Advanced risk analytics and fleet-wide KPI insights
          </p>
        </div>
        <div className="flex rounded-xl bg-slate-100 p-0.5">
          {ranges.map((r) => (
            <button
              key={r}
              onClick={() => setRange(r)}
              className={`px-3.5 py-1.5 rounded-[10px] text-xs font-medium transition-all ${
                range === r
                  ? "bg-white text-slate-800 shadow-sm"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              {r}d
            </button>
          ))}
        </div>
        <button
          onClick={() => generateExecutiveReport(dashboard, trends)}
          disabled={loading || !dashboard}
          className="btn-primary shrink-0"
        >
          <DocumentArrowDownIcon className="h-4 w-4" />
          Export Executive Report
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3.5 rounded-xl bg-red-50 border border-red-200/60 text-sm text-red-600 font-medium">
          <ExclamationTriangleIcon className="h-4 w-4 shrink-0" />
          {error}. Some data may be unavailable.
        </div>
      )}

      {/* Risk trend area chart */}
      <div className="card">
        <h2 className="section-title mb-6">Aggregate Risk Trajectory</h2>
        <ResponsiveContainer width="100%" height={320}>
          <AreaChart data={trends} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#0ea5e9" stopOpacity={0.7} />
                <stop offset="100%" stopColor="#0ea5e9" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="4 4" stroke="#64748b" vertical={false} opacity={0.15} />
            <XAxis dataKey="date" tick={{ fontSize: 12, fill: '#64748b', fontWeight: 500 }} axisLine={false} tickLine={false} dy={10} />
            <YAxis tick={{ fontSize: 12, fill: '#64748b', fontWeight: 500 }} domain={[0, 1]} axisLine={false} tickLine={false} dx={-10} />
            <Tooltip content={<ChartTooltip />} />
            <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 12, paddingTop: '20px' }} />
            <Area
              type="monotone"
              dataKey="avg_risk"
              stroke="#0ea5e9"
              strokeWidth={3}
              fill="url(#riskGrad)"
              name="Avg Risk"
              isAnimationActive={false}
            />
            <Line
              type="monotone"
              dataKey="max_risk"
              stroke="#f43f5e"
              strokeWidth={3}
              dot={false}
              name="Max Risk"
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Equipment health comparison */}
      <div className="card">
        <h2 className="section-title mb-6">Asset Deterioration Spectrum</h2>
        {healthData.length > 0 ? (
          <ResponsiveContainer width="100%" height={Math.max(300, healthData.length * 40)}>
            <BarChart data={healthData} layout="vertical" barSize={16}>
              <defs>
                <linearGradient id="riskGradBar" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#f59e0b" />
                  <stop offset="100%" stopColor="#f43f5e" />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="4 4" stroke="#64748b" horizontal={false} opacity={0.15} />
              <XAxis type="number" domain={[0, 1]} tick={{ fontSize: 12, fill: '#64748b', fontWeight: 500 }} axisLine={false} tickLine={false} />
              <YAxis
                type="category"
                dataKey="equipment_name"
                width={150}
                tick={{ fontSize: 12, fill: '#64748b', fontWeight: 500 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<ChartTooltip />} />
              <Bar
                dataKey="risk_score"
                fill="url(#riskGradBar)"
                radius={[0, 8, 8, 0]}
                name="Risk Score"
                isAnimationActive={false}
              />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="empty-state h-[300px]">
            <ChartBarSquareIcon className="h-10 w-10 text-slate-300 mx-auto mb-3" />
            <p className="text-sm text-slate-400">No equipment health data available</p>
          </div>
        )}
      </div>

      {/* Summary stats */}
      {dashboard && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 xl:gap-6 mt-2">
          <div className="card !p-5 flex flex-col justify-between hover:-translate-y-1 transition-transform">
            <p className="text-xs font-bold text-slate-500 tracking-wider uppercase">Inference Volume</p>
            <div className="mt-4 flex items-baseline gap-2">
              <span className="text-4xl font-extrabold text-slate-900 dark:text-white tracking-tighter">{dashboard.predictions_today || 0}</span>
              <span className="text-sm font-medium text-slate-500">today</span>
            </div>
          </div>
          <div className="card !p-5 flex flex-col justify-between hover:-translate-y-1 transition-transform">
            <p className="text-xs font-bold text-slate-500 tracking-wider uppercase">Alarm Frequency</p>
            <div className="mt-4 flex items-baseline gap-2">
              <span className="text-4xl font-extrabold text-slate-900 dark:text-white tracking-tighter">{dashboard.alerts_this_week || 0}</span>
              <span className="text-sm font-medium text-slate-500">this week</span>
            </div>
          </div>
          <div className="card !p-5 flex flex-col justify-between hover:-translate-y-1 transition-transform">
            <p className="text-xs font-bold text-slate-500 tracking-wider uppercase">Model Precision</p>
            <div className="mt-4 flex items-baseline gap-2">
              <span className="text-4xl font-extrabold text-slate-900 dark:text-white tracking-tighter">
                {dashboard.model_accuracy ? `${(dashboard.model_accuracy * 100).toFixed(1)}%` : "N/A"}
              </span>
              <span className="text-sm font-medium text-slate-500">F1 Score</span>
            </div>
          </div>
          <div className="card !p-5 flex flex-col justify-between hover:-translate-y-1 transition-transform">
            <p className="text-xs font-bold text-slate-500 tracking-wider uppercase">System Uptime</p>
            <div className="mt-4 flex items-baseline gap-2">
              <span className="text-4xl font-extrabold text-slate-900 dark:text-white tracking-tighter">99.9</span>
              <span className="text-sm font-medium text-slate-500">%</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
