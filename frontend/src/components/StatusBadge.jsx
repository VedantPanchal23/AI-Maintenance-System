import { cn } from "@/lib/utils";

const severityStyles = {
  critical: "bg-red-50 dark:bg-red-500/10 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-500/20",
  high: "bg-orange-50 dark:bg-orange-500/10 text-orange-700 dark:text-orange-400 border border-orange-200 dark:border-orange-500/20",
  medium: "bg-yellow-50 dark:bg-yellow-500/10 text-yellow-700 dark:text-yellow-400 border border-yellow-200 dark:border-yellow-500/20",
  low: "bg-green-50 dark:bg-green-500/10 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-500/20",
};

const statusStyles = {
  operational: "bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20",
  warning: "bg-yellow-50 dark:bg-yellow-500/10 text-yellow-700 dark:text-yellow-400 border border-yellow-200 dark:border-yellow-500/20",
  critical: "bg-red-50 dark:bg-red-500/10 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-500/20",
  maintenance: "bg-brand-50 dark:bg-brand-500/10 text-brand-700 dark:text-brand-400 border border-brand-200 dark:border-brand-500/20",
  offline: "bg-slate-100 dark:bg-slate-500/10 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-500/20",
  active: "bg-red-50 dark:bg-red-500/10 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-500/20",
  acknowledged: "bg-yellow-50 dark:bg-yellow-500/10 text-yellow-700 dark:text-yellow-400 border border-yellow-200 dark:border-yellow-500/20",
  resolved: "bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20",
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
        "badge gap-2 font-bold tracking-wide",
        severityStyles[level] || "bg-slate-100 text-slate-600",
        className
      )}
    >
      <span className="relative flex h-1.5 w-1.5">
        <span className={cn("animate-ping absolute inline-flex h-full w-full rounded-full opacity-75", {
          "bg-red-400": level === "critical",
          "bg-orange-400": level === "high",
          "bg-yellow-400": level === "medium",
          "bg-green-400": level === "low",
        })} />
        <span
          className={cn("relative inline-flex rounded-full h-1.5 w-1.5", {
            "bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)]": level === "critical",
            "bg-orange-500 shadow-[0_0_8px_rgba(249,115,22,0.8)]": level === "high",
            "bg-yellow-500 shadow-[0_0_8px_rgba(234,179,8,0.8)]": level === "medium",
            "bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.8)]": level === "low",
          })}
        />
      </span>
      {probability !== undefined ? `${(probability * 100).toFixed(1)}%` : level}
    </span>
  );
}
