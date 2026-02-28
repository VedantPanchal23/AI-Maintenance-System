import { SeverityBadge, StatusBadge } from "./StatusBadge";
import { formatDate, timeAgo } from "@/lib/utils";
import { ExclamationTriangleIcon } from "@heroicons/react/24/solid";

/**
 * Single alert card with details and action buttons
 */
export default function AlertCard({ alert, onAcknowledge, onResolve }) {
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

  const severityIcon = {
    critical: "bg-red-50 text-red-600",
    high: "bg-orange-50 text-orange-600",
    medium: "bg-yellow-50 text-yellow-600",
    low: "bg-green-50 text-green-600",
  };
  const iconStyle = severityIcon[severity] || severityIcon.medium;

  return (
    <div className="card animate-fade-in">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 min-w-0">
          <div
            className={`flex h-9 w-9 items-center justify-center rounded-lg shrink-0 ${iconStyle.split(" ")[0]}`}
          >
            <ExclamationTriangleIcon
              className={`h-5 w-5 ${iconStyle.split(" ").slice(1).join(" ")}`}
            />
          </div>
          <div className="min-w-0">
            <h3 className="text-sm font-semibold text-slate-900 truncate">
              {title || "Equipment Alert"}
            </h3>
            <p className="text-xs text-slate-500 mt-0.5 truncate">
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
        <p className="mt-3 text-sm text-slate-600 leading-relaxed">{message}</p>
      )}

      {failure_probability != null && (
        <div className="mt-3 flex items-center gap-3">
          <div className="flex-1 bg-slate-100 rounded-full h-1.5">
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
          <span className="text-xs font-semibold text-slate-700 tabular-nums w-12 text-right">
            {(failure_probability * 100).toFixed(1)}%
          </span>
        </div>
      )}

      {/* Actions */}
      {status === "active" && (
        <div className="mt-4 pt-4 border-t border-slate-100 flex gap-2">
          <button
            onClick={() => onAcknowledge?.(id)}
            className="btn-ghost text-xs py-1.5 px-3"
          >
            Acknowledge
          </button>
          <button
            onClick={() => onResolve?.(id)}
            className="btn-primary text-xs py-1.5 px-3"
          >
            Resolve
          </button>
        </div>
      )}
      {status === "acknowledged" && (
        <div className="mt-4 pt-4 border-t border-slate-100">
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
