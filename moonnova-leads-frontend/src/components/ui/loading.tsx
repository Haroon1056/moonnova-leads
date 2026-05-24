import { Loader2 } from "lucide-react";

export function PageLoader() {
  return (
    <div className="flex min-h-[300px] items-center justify-center rounded-2xl border border-borderSoft bg-white/70">
      <div className="flex items-center gap-3 text-sm font-semibold text-slate-600">
        <Loader2 className="h-5 w-5 animate-spin text-primary" />
        Loading workspace...
      </div>
    </div>
  );
}

export function TableSkeleton({ rows = 6 }: { rows?: number }) {
  return (
    <div className="space-y-3 p-4">
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="grid gap-3 md:grid-cols-5">
          <div className="skeleton h-9 rounded-xl md:col-span-2" />
          <div className="skeleton h-9 rounded-xl" />
          <div className="skeleton h-9 rounded-xl" />
          <div className="skeleton h-9 rounded-xl" />
        </div>
      ))}
    </div>
  );
}
