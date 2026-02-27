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
      <div className="card-hover cursor-pointer">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50">
              <CpuChipIcon className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-900">{name}</h3>
              <p className="text-xs text-slate-500 capitalize">
                {equipment_type?.replace(/_/g, " ")} • {location || "—"}
              </p>
            </div>
          </div>
          <StatusBadge status={status || "operational"} />
        </div>

        <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
          <div>
            <p className="text-xs text-slate-500">Risk</p>
            {latest_risk_score !== undefined ? (
              <RiskBadge
                level={latest_risk_level || "low"}
                probability={latest_risk_score}
              />
            ) : (
              <span className="text-xs text-slate-400">No data</span>
            )}
          </div>
          <div>
            <p className="text-xs text-slate-500">Last Reading</p>
            <p className="text-xs text-slate-700">
              {last_reading_at ? formatDate(last_reading_at) : "—"}
            </p>
          </div>
        </div>
      </div>
    </Link>
  );
}
