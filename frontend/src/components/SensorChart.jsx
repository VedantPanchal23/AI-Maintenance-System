"use client";

import { memo, useState } from "react";
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

function CustomLegend({ payload, onClick, hidden }) {
  return (
    <div className="flex flex-wrap gap-3 pt-6 justify-center">
      {payload.map((entry) => {
        const isHidden = hidden[entry.dataKey];
        return (
          <button 
            key={entry.value} 
            onClick={() => onClick(entry.dataKey)}
            className={`flex items-center gap-2 text-[0.6875rem] font-bold tracking-wider uppercase px-2.5 py-1.5 rounded-lg border transition-all duration-300 ${
              isHidden 
                ? 'opacity-40 grayscale border-transparent hover:opacity-70 bg-transparent' 
                : 'border-slate-200 dark:border-white/[0.08] bg-slate-50 dark:bg-white/[0.04] shadow-sm hover:bg-slate-100 dark:hover:bg-white/[0.08]'
            }`}
          >
            <span className="w-2.5 h-2.5 rounded-full shadow-inner" style={{ backgroundColor: entry.color }} />
            <span className={isHidden ? 'text-slate-500' : 'text-slate-700 dark:text-slate-200'}>{entry.value}</span>
          </button>
        );
      })}
    </div>
  );
}

/**
 * Real-time sensor chart with God-Tier interactive toggles
 */
const SensorChart = memo(function SensorChart({
  data = [],
  sensors = ["air_temperature", "process_temperature"],
  height = 300,
}) {
  const [hidden, setHidden] = useState({});

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

  const toggleSeries = (dataKey) => {
    setHidden((prev) => ({ ...prev, [dataKey]: !prev[dataKey] }));
  };

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
          content={<CustomLegend hidden={hidden} onClick={toggleSeries} />}
        />
        {sensors.map((key) => (
          <Area
            key={key}
            type="monotone"
            dataKey={key}
            hide={hidden[key]}
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
