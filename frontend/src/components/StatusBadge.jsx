import { cn } from "@/lib/utils";

const severityStyles = {
  critical: "bg-red-50 text-red-700 ring-1 ring-red-600/10",
  high: "bg-orange-50 text-orange-700 ring-1 ring-orange-600/10",
  medium: "bg-yellow-50 text-yellow-700 ring-1 ring-yellow-600/10",
  low: "bg-green-50 text-green-700 ring-1 ring-green-600/10",
};

const statusStyles = {
  operational: "bg-emerald-50 text-emerald-700",
  warning: "bg-yellow-50 text-yellow-700",
  critical: "bg-red-50 text-red-700",
  maintenance: "bg-brand-50 text-brand-700",
  offline: "bg-slate-100 text-slate-600",
  active: "bg-red-50 text-red-700",
  acknowledged: "bg-yellow-50 text-yellow-700",
  resolved: "bg-emerald-50 text-emerald-700",
};

export function StatusBadge({ status, className }) {
  return (
    <span
      className={cn(
        "badge",
        statusStyles[status] || "bg-gray-100 text-gray-600",
        className
      )}
    >
      {status}
    </span>
  );
}

export function SeverityBadge({ severity, className }) {
  return (
    <span
      className={cn(
        "badge",
        severityStyles[severity] || "bg-gray-100 text-gray-600",
        className
      )}
    >
      {severity}
    </span>
  );
}

export function RiskBadge({ level, probability, className }) {
  return (
    <span
      className={cn(
        "badge gap-1",
        severityStyles[level] || "bg-gray-100 text-gray-600",
        className
      )}
    >
      <span
        className={cn("h-1.5 w-1.5 rounded-full", {
          "bg-red-500": level === "critical",
          "bg-orange-500": level === "high",
          "bg-yellow-500": level === "medium",
          "bg-green-500": level === "low",
        })}
      />
      {probability !== undefined ? `${(probability * 100).toFixed(1)}%` : level}
    </span>
  );
}
