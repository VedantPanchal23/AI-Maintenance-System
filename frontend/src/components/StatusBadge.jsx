import { cn } from "@/lib/utils";

const severityStyles = {
  critical: "bg-red-100 text-red-800 ring-1 ring-red-600/20",
  high: "bg-orange-100 text-orange-800 ring-1 ring-orange-600/20",
  medium: "bg-yellow-100 text-yellow-800 ring-1 ring-yellow-600/20",
  low: "bg-green-100 text-green-800 ring-1 ring-green-600/20",
};

const statusStyles = {
  operational: "bg-green-100 text-green-800",
  warning: "bg-yellow-100 text-yellow-800",
  critical: "bg-red-100 text-red-800",
  maintenance: "bg-blue-100 text-blue-800",
  offline: "bg-gray-100 text-gray-800",
  active: "bg-red-100 text-red-800",
  acknowledged: "bg-yellow-100 text-yellow-800",
  resolved: "bg-green-100 text-green-800",
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
