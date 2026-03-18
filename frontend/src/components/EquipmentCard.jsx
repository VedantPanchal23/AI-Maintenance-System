import Link from "next/link";
import { StatusBadge, RiskBadge } from "./StatusBadge";
import { CpuChipIcon } from "@heroicons/react/24/outline";
import { formatDate } from "@/lib/utils";

/**
 * Card displaying a single equipment unit with status and latest risk
 */
export default function EquipmentCard({ equipment }) {
  if (!equipment) return null;

  const {
    id,
    name,
    equipment_type,
    status,
    location,
    latest_risk_score,
    latest_risk_level,
    last_reading_at,
  } = equipment;

  return (
    <Link href={`/equipment/${id}`}>
      <div className="card group cursor-pointer transition-shadow hover:shadow-card-hover">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-50 dark:bg-brand-900/40 shrink-0 transition-colors group-hover:bg-brand-100 dark:group-hover:bg-brand-900/60">
              <CpuChipIcon className="h-5 w-5 text-brand-600 dark:text-brand-400" />
            </div>
            <div className="min-w-0">
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white truncate">{name}</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 capitalize truncate">
                {equipment_type?.replace(/_/g, " ")} &middot; {location || "\u2014"}
              </p>
            </div>
          </div>
          <StatusBadge status={status || "operational"} />
        </div>

        <div className="mt-4 pt-4 border-t border-slate-100 dark:border-surface-800/60 grid grid-cols-2 gap-3 text-sm">
          <div>
            <p className="text-2xs text-slate-400 uppercase tracking-wider mb-1">Risk</p>
            {latest_risk_score != null ? (
              <RiskBadge
                level={latest_risk_level || "low"}
                probability={latest_risk_score}
              />
            ) : (
              <span className="text-xs text-slate-400">No data</span>
            )}
          </div>
          <div>
            <p className="text-2xs text-slate-400 uppercase tracking-wider mb-1">Last Reading</p>
            <p className="text-xs text-slate-700 dark:text-slate-300 tabular-nums">
              {last_reading_at ? formatDate(last_reading_at) : "\u2014"}
            </p>
          </div>
        </div>
      </div>
    </Link>
  );
}
