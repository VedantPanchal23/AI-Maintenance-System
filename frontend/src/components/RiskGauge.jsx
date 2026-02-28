"use client";

/**
 * Radial gauge for displaying risk / health percentage
 */
export default function RiskGauge({ value = 0, size = 120, label = "Risk" }) {
  // Expect value in 0–100 scale (caller should pre-multiply if needed)
  const normalised = value;
  const radius = (size - 16) / 2;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.min(Math.max(normalised, 0), 100);
  const offset = circumference - (clamped / 100) * circumference;

  let colorClass = "gauge-low";
  if (clamped >= 75) colorClass = "gauge-critical";
  else if (clamped >= 50) colorClass = "gauge-high";
  else if (clamped >= 25) colorClass = "gauge-medium";

  return (
    <div className="relative flex flex-col items-center">
      <svg width={size} height={size} className="-rotate-90">
        {/* Background */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={8}
          fill="none"
          className="gauge-bg"
        />
        {/* Value arc */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={8}
          fill="none"
          strokeLinecap="round"
          className={colorClass}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
      </svg>
      <div
        className="absolute flex flex-col items-center justify-center"
        style={{ width: size, height: size }}
      >
        <span className="text-xl font-bold text-slate-900 tabular-nums">
          {clamped.toFixed(0)}%
        </span>
        <span className="text-2xs text-slate-400 uppercase tracking-wider">{label}</span>
      </div>
    </div>
  );
}
