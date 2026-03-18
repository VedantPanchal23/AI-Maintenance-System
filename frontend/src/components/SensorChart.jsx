"use client";

import { memo } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { SignalIcon } from "@heroicons/react/24/outline";

const SENSOR_COLORS = {
  air_temperature: "#3b82f6",
  process_temperature: "#ef4444",
  rotational_speed: "#8b5cf6",
  torque: "#f59e0b",
  tool_wear: "#10b981",
  vibration: "#06b6d4",
  power_consumption: "#ec4899",
};

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl bg-white dark:bg-surface-800 px-4 py-3 shadow-elevated border border-slate-200/60 dark:border-surface-700/60">
      <p className="text-2xs text-slate-500 dark:text-slate-400 mb-1.5">
        {new Date(label).toLocaleString("en-IN")}
      </p>
      {payload.map((entry) => (
        <div key={entry.dataKey} className="flex items-center gap-2 text-xs">
          <span
            className="h-2 w-2 rounded-full shrink-0"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-slate-600 dark:text-slate-300 capitalize">
            {entry.name}
          </span>
          <span className="ml-auto font-semibold tabular-nums text-slate-900 dark:text-slate-100">
            {typeof entry.value === "number" ? entry.value.toFixed(1) : entry.value}
          </span>
        </div>
      ))}
    </div>
  );
}

/**
 * Real-time sensor chart for a single equipment
 */
const SensorChart = memo(function SensorChart({
  data = [],
  sensors = ["air_temperature", "process_temperature"],
  height = 300,
}) {
  if (!data.length) {
    return (
      <div
        className="flex flex-col items-center justify-center gap-2 text-sm text-slate-400 dark:text-slate-500"
        style={{ height }}
      >
        <SignalIcon className="h-8 w-8 text-slate-300 dark:text-slate-600" />
        No sensor data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
        <defs>
          {sensors.map((key) => (
            <linearGradient key={`color-${key}`} id={`color-${key}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={SENSOR_COLORS[key] || "#6b7280"} stopOpacity={0.4} />
              <stop offset="95%" stopColor={SENSOR_COLORS[key] || "#6b7280"} stopOpacity={0} />
            </linearGradient>
          ))}
        </defs>
        <CartesianGrid vertical={false} stroke="#64748b" strokeDasharray="3 3" opacity={0.15} />
        <XAxis
          dataKey="timestamp"
          tick={{ fontSize: 11, fill: "#94a3b8" }}
          axisLine={false}
          tickLine={false}
          tickFormatter={(v) =>
            new Date(v).toLocaleTimeString("en-IN", {
              hour: "2-digit",
              minute: "2-digit",
            })
          }
        />
        <YAxis
          tick={{ fontSize: 11, fill: "#94a3b8" }}
          axisLine={false}
          tickLine={false}
          width={45}
        />
        <Tooltip content={<ChartTooltip />} />
        <Legend
          wrapperStyle={{ fontSize: 12, paddingTop: 8 }}
          iconType="circle"
          iconSize={8}
        />
        {sensors.map((key) => (
          <Area
            key={key}
            type="monotone"
            dataKey={key}
            stroke={SENSOR_COLORS[key] || "#6b7280"}
            fill={`url(#color-${key})`}
            strokeWidth={2}
            isAnimationActive={false}
            name={key.replace(/_/g, " ")}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  );
});

export default SensorChart;
