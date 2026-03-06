"use client";

import { useEffect, useState } from "react";
import { analyticsAPI } from "@/lib/api";
import { PageSpinner } from "@/components/Loading";
import ChartTooltip from "@/components/ChartTooltip";
import {
  ChartBarSquareIcon,
  ExclamationTriangleIcon,
} from "@heroicons/react/24/outline";
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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="page-title">Analytics</h1>
          <p className="page-subtitle">
            Advanced risk analytics and equipment health insights
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
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3.5 rounded-xl bg-red-50 border border-red-200/60 text-sm text-red-600 font-medium">
          <ExclamationTriangleIcon className="h-4 w-4 shrink-0" />
          {error}. Some data may be unavailable.
        </div>
      )}

      {/* Risk trend area chart */}
      <div className="card">
        <h2 className="section-title mb-4">Risk Score Trend</h2>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={trends}>
            <defs>
              <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="#94a3b8" axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" domain={[0, 1]} axisLine={false} tickLine={false} />
            <Tooltip content={<ChartTooltip />} />
            <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 12 }} />
            <Area
              type="monotone"
              dataKey="avg_risk"
              stroke="#3b82f6"
              strokeWidth={2}
              fill="url(#riskGrad)"
              name="Avg Risk"
            />
            <Line
              type="monotone"
              dataKey="max_risk"
              stroke="#ef4444"
              strokeWidth={2}
              dot={false}
              name="Max Risk"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Equipment health comparison */}
      <div className="card">
        <h2 className="section-title mb-4">Equipment Health Comparison</h2>
        {healthData.length > 0 ? (
          <ResponsiveContainer width="100%" height={Math.max(300, healthData.length * 36)}>
            <BarChart data={healthData} layout="vertical" barSize={16}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
              <XAxis type="number" domain={[0, 1]} tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis
                type="category"
                dataKey="equipment_name"
                width={140}
                tick={{ fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<ChartTooltip />} />
              <Bar
                dataKey="risk_score"
                fill="#f97316"
                radius={[0, 6, 6, 0]}
                name="Risk Score"
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
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="stat-card">
            <span className="stat-label">Predictions Today</span>
            <span className="stat-value">{dashboard.predictions_today || 0}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Alerts This Week</span>
            <span className="stat-value">{dashboard.alerts_this_week || 0}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Model Accuracy</span>
            <span className="stat-value">
              {dashboard.model_accuracy ? `${(dashboard.model_accuracy * 100).toFixed(1)}%` : "N/A"}
            </span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Uptime</span>
            <span className="stat-value">{dashboard.system_uptime || "N/A"}</span>
          </div>
        </div>
      )}
    </div>
  );
}
