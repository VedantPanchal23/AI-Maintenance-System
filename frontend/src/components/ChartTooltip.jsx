/**
 * Shared custom tooltip for Recharts charts.
 * Extracted to avoid re-creating inside render functions.
 */
export default function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl bg-white px-3 py-2 shadow-elevated border border-slate-100 text-xs">
      <p className="font-medium text-slate-700 mb-1">{label}</p>
      {payload.map((p) => (
        <p key={p.dataKey} className="text-slate-500">
          <span
            className="inline-block w-2 h-2 rounded-full mr-1.5"
            style={{ background: p.fill || p.color }}
          />
          {p.name || p.dataKey}:{" "}
          <span className="font-semibold text-slate-700">
            {typeof p.value === "number" ? p.value.toFixed(2) : p.value}
          </span>
        </p>
      ))}
    </div>
  );
}
