import { SeverityBadge, StatusBadge } from "./StatusBadge";
import { formatDate, timeAgo } from "@/lib/utils";
import { ExclamationTriangleIcon } from "@heroicons/react/24/solid";

/**
 * Single alert card with details and action buttons
 */
export default function AlertCard({ alert, onAcknowledge, onResolve, onCreateTicket }) {
  if (!alert) return null;

  const {
    id,
    title,
    message,
    severity,
    status,
    equipment_name,
    failure_type,
    failure_probability,
    created_at,
  } = alert;

  const severityStyles = {
    critical: { bg: "bg-red-50 dark:bg-red-500/10", text: "text-red-600 dark:text-red-400" },
    high: { bg: "bg-orange-50 dark:bg-orange-500/10", text: "text-orange-600 dark:text-orange-400" },
    medium: { bg: "bg-yellow-50 dark:bg-yellow-500/10", text: "text-yellow-600 dark:text-yellow-400" },
    low: { bg: "bg-green-50 dark:bg-green-500/10", text: "text-green-600 dark:text-green-400" },
  };
  const { bg, text } = severityStyles[severity] || severityStyles.medium;

  return (
    <div className="card animate-fade-in">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 min-w-0">
          <div
            className={`flex h-9 w-9 items-center justify-center rounded-lg shrink-0 ${bg}`}
          >
            <ExclamationTriangleIcon
              className={`h-5 w-5 ${text}`}
            />
          </div>
          <div className="min-w-0">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white truncate">
              {title || "Equipment Alert"}
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 truncate">
              {equipment_name} &middot; {failure_type?.replace(/_/g, " ") || "Unknown"} &middot;{" "}
              {timeAgo(created_at)}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          <SeverityBadge severity={severity} />
          <StatusBadge status={status} />
        </div>
      </div>

      {message && (
        <p className="mt-3 text-sm text-slate-600 dark:text-slate-300 leading-relaxed">{message}</p>
      )}

      {failure_probability != null && (
        <div className="mt-3 flex items-center gap-3">
          <div className="flex-1 bg-slate-100 dark:bg-surface-800 rounded-full h-1.5">
            <div
              className={`h-1.5 rounded-full transition-all duration-500 ${
                failure_probability >= 0.75
                  ? "bg-red-500"
                  : failure_probability >= 0.5
                  ? "bg-orange-500"
                  : "bg-yellow-500"
              }`}
              style={{ width: `${(failure_probability * 100).toFixed(0)}%` }}
            />
          </div>
          <span className="text-xs font-semibold text-slate-700 dark:text-slate-300 tabular-nums w-12 text-right">
            {(failure_probability * 100).toFixed(1)}%
          </span>
        </div>
      )}

      {/* Actions */}
      {status === "active" && (
        <div className="mt-4 pt-4 border-t border-slate-100 dark:border-surface-800/60 flex flex-wrap gap-2">
          <button
            onClick={() => onAcknowledge?.(id)}
            className="btn-ghost text-xs py-1.5 px-3"
          >
            Acknowledge
          </button>
          {onCreateTicket && (
            <button
              onClick={() => onCreateTicket?.(alert)}
              className="btn-secondary text-xs py-1.5 px-3 bg-indigo-50 dark:bg-indigo-500/10 text-indigo-700 dark:text-indigo-400 font-semibold"
            >
              Create Ticket
            </button>
          )}
          <button
            onClick={() => onResolve?.(id)}
            className="btn-primary text-xs py-1.5 px-3"
          >
            Resolve
          </button>
        </div>
      )}
      {status === "acknowledged" && (
        <div className="mt-4 pt-4 border-t border-slate-100 dark:border-surface-800/60 flex gap-2">
          {onCreateTicket && (
            <button
              onClick={() => onCreateTicket?.(alert)}
              className="btn-secondary text-xs py-1.5 px-3 bg-indigo-50 dark:bg-indigo-500/10 text-indigo-700 dark:text-indigo-400 font-semibold"
            >
              Create Ticket
            </button>
          )}
          <button
            onClick={() => onResolve?.(id)}
            className="btn-primary text-xs py-1.5 px-3"
          >
            Mark Resolved
          </button>
        </div>
      )}
    </div>
  );
}
