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

const SENSOR_COLORS = {
  air_temperature: "#3b82f6",
  process_temperature: "#ef4444",
  rotational_speed: "#8b5cf6",
  torque: "#f59e0b",
  tool_wear: "#10b981",
  vibration: "#06b6d4",
  power_consumption: "#ec4899",
};

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
        className="flex items-center justify-center text-sm text-slate-400"
        style={{ height }}
      >
        No sensor data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis
          dataKey="timestamp"
          tick={{ fontSize: 11 }}
          stroke="#94a3b8"
          tickFormatter={(v) =>
            new Date(v).toLocaleTimeString("en-IN", {
              hour: "2-digit",
              minute: "2-digit",
            })
          }
        />
        <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" />
        <Tooltip
          contentStyle={{
            background: "#fff",
            border: "1px solid #e2e8f0",
            borderRadius: 8,
            fontSize: 12,
          }}
          labelFormatter={(v) => new Date(v).toLocaleString("en-IN")}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
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
