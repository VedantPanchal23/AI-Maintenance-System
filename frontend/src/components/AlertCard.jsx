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

  return (
    <div className="card animate-fade-in">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <div
            className={`flex h-9 w-9 items-center justify-center rounded-lg ${
              severity === "critical"
                ? "bg-red-100"
                : severity === "high"
                ? "bg-orange-100"
                : "bg-yellow-100"
            }`}
          >
            <ExclamationTriangleIcon
              className={`h-5 w-5 ${
                severity === "critical"
                  ? "text-red-600"
                  : severity === "high"
                  ? "text-orange-600"
                  : "text-yellow-600"
              }`}
            />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-900">
              {title || "Equipment Alert"}
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              {equipment_name} • {failure_type?.replace(/_/g, " ") || "Unknown"} •{" "}
              {timeAgo(created_at)}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <SeverityBadge severity={severity} />
          <StatusBadge status={status} />
        </div>
      </div>

      {message && (
        <p className="mt-3 text-sm text-slate-600 leading-relaxed">{message}</p>
      )}

      {failure_probability !== undefined && (
        <div className="mt-3 flex items-center gap-3">
          <div className="flex-1 bg-slate-100 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all ${
                failure_probability >= 0.75
                  ? "bg-red-500"
                  : failure_probability >= 0.5
                  ? "bg-orange-500"
                  : "bg-yellow-500"
              }`}
              style={{ width: `${(failure_probability * 100).toFixed(0)}%` }}
            />
          </div>
          <span className="text-xs font-medium text-slate-600">
            {(failure_probability * 100).toFixed(1)}%
          </span>
        </div>
      )}

      {/* Actions */}
      {status === "active" && (
        <div className="mt-4 flex gap-2">
          <button
            onClick={() => onAcknowledge?.(id)}
            className="btn-secondary text-xs py-1.5 px-3"
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
        <div className="mt-4">
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
