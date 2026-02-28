"use client";

import {
  LineChart,
  Line,
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
    <div className="rounded-xl bg-white px-4 py-3 shadow-elevated border border-slate-200/60">
      <p className="text-2xs text-slate-500 mb-1.5">
        {new Date(label).toLocaleString("en-IN")}
      </p>
      {payload.map((entry) => (
        <div key={entry.dataKey} className="flex items-center gap-2 text-xs">
          <span
            className="h-2 w-2 rounded-full shrink-0"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-slate-600 capitalize">{entry.name}</span>
          <span className="ml-auto font-semibold tabular-nums text-slate-900">
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
export default function SensorChart({
  data = [],
  sensors = ["air_temperature", "process_temperature"],
  height = 300,
}) {
  if (!data.length) {
    return (
      <div
        className="flex flex-col items-center justify-center gap-2 text-sm text-slate-400"
        style={{ height }}
      >
        <SignalIcon className="h-8 w-8 text-slate-300" />
        No sensor data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
        <CartesianGrid vertical={false} stroke="#f1f5f9" />
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
          <Line
            key={key}
            type="monotone"
            dataKey={key}
            stroke={SENSOR_COLORS[key] || "#6b7280"}
            strokeWidth={2}
            dot={false}
            name={key.replace(/_/g, " ")}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
