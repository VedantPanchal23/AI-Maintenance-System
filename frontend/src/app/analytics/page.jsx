"use client";

import { useEffect, useState } from "react";
import { analyticsAPI } from "@/lib/api";
import { PageSpinner } from "@/components/Loading";
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
  const [range, setRange] = useState(7);

  useEffect(() => {
    setLoading(true);
    async function load() {
      try {
        const [dashRes, trendRes] = await Promise.all([
          analyticsAPI.dashboard(),
          analyticsAPI.riskTrends({ hours: range * 24 }),
        ]);
        setDashboard(dashRes.data);
        setTrends(trendRes.data || []);
      } catch (err) {
        console.error("Analytics load failed:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [range]);

  if (loading) return <PageSpinner />;

  const healthData = dashboard?.equipment_health || [];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Analytics</h1>
          <p className="text-sm text-slate-500 mt-1">
            Advanced risk analytics and equipment health insights
          </p>
        </div>
        <select
          value={range}
          onChange={(e) => setRange(Number(e.target.value))}
          className="input-field w-auto"
        >
          <option value={7}>Last 7 days</option>
          <option value={14}>Last 14 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      {/* Risk trend area chart */}
      <div className="card">
        <h2 className="text-sm font-semibold text-slate-900 mb-4">
          Risk Score Trend
        </h2>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={trends}>
            <defs>
              <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="#94a3b8" />
            <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" domain={[0, 1]} />
            <Tooltip />
            <Legend />
            <Area
              type="monotone"
              dataKey="avg_risk"
              stroke="#3b82f6"
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
        <h2 className="text-sm font-semibold text-slate-900 mb-4">
          Equipment Health Comparison
        </h2>
        {healthData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={healthData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis type="number" domain={[0, 1]} tick={{ fontSize: 11 }} />
              <YAxis
                type="category"
                dataKey="name"
                width={140}
                tick={{ fontSize: 11 }}
              />
              <Tooltip />
              <Bar
                dataKey="risk_score"
                fill="#f97316"
                radius={[0, 4, 4, 0]}
                name="Risk Score"
              />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-[300px] text-sm text-slate-400">
            No equipment health data available
          </div>
        )}
      </div>

      {/* Summary stats */}
      {dashboard && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="stat-card">
            <span className="stat-label">Predictions Today</span>
            <span className="stat-value">
              {dashboard.predictions_today || 0}
            </span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Alerts This Week</span>
            <span className="stat-value">
              {dashboard.alerts_this_week || 0}
            </span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Model Accuracy</span>
            <span className="stat-value">
              {dashboard.model_accuracy
                ? `${(dashboard.model_accuracy * 100).toFixed(1)}%`
                : "N/A"}
            </span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Uptime</span>
            <span className="stat-value">
              {dashboard.system_uptime || "N/A"}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
