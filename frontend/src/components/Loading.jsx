/**
 * Loading spinner and skeleton components
 */

export function Spinner({ size = "md" }) {
  const sizes = { sm: "h-5 w-5", md: "h-8 w-8", lg: "h-12 w-12" };
  return (
    <div className="flex items-center justify-center p-8">
      <div
        className={`animate-spin ${sizes[size]} border-2 border-brand-600 border-t-transparent rounded-full`}
      />
    </div>
  );
}

export function PageSpinner() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="flex flex-col items-center gap-3">
        <div className="animate-spin h-10 w-10 border-[3px] border-brand-600 border-t-transparent rounded-full" />
        <p className="text-sm text-slate-400">Loading\u2026</p>
      </div>
    </div>
  );
}

export function CardSkeleton() {
  return (
    <div className="card animate-pulse">
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 bg-slate-100 rounded-lg" />
        <div className="flex-1">
          <div className="h-4 bg-slate-100 rounded w-1/3 mb-2" />
          <div className="h-3 bg-slate-100 rounded w-1/2" />
        </div>
      </div>
      <div className="mt-4 pt-4 border-t border-slate-100 grid grid-cols-2 gap-3">
        <div className="h-8 bg-slate-100 rounded" />
        <div className="h-8 bg-slate-100 rounded" />
      </div>
    </div>
  );
}

export function StatSkeleton() {
  return (
    <div className="stat-card animate-pulse">
      <div className="h-3 bg-slate-100 rounded w-1/3 mb-3" />
      <div className="h-7 bg-slate-100 rounded w-1/2" />
    </div>
  );
}
