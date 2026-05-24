import { Activity, Archive, Database, Download, ShieldCheck, TrendingUp, WalletCards } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PageLoader } from "@/components/ui/loading";
import { useUsage } from "@/hooks/useUsage";

function pct(used?: number | null, max?: number | null, unlimited?: boolean) {
  if (unlimited) return 8;
  if (!used || !max) return 0;
  return Math.min(100, Math.round((used / max) * 100));
}
function n(value?: number | null) { return typeof value === "number" ? value.toLocaleString() : "0"; }

function UsageMeter({ title, used, limit, remaining, unlimited, icon: Icon }: any) {
  const percent = pct(used, limit, unlimited);
  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm font-bold text-slate-500">{title}</p>
            <p className="mt-2 text-3xl font-black text-slate-950">{n(used)}</p>
            <p className="mt-1 text-xs font-medium text-slate-500">
              {unlimited ? "Unlimited plan" : `${n(remaining)} remaining • limit ${n(limit)}`}
            </p>
          </div>
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primarySoft text-primaryDark ring-1 ring-orange-200"><Icon className="h-5 w-5" /></div>
        </div>
        <div className="mt-5 h-2.5 rounded-full bg-stone-100">
          <div className="h-2.5 rounded-full bg-gradient-to-r from-amber-600 to-teal-700" style={{ width: `${percent}%` }} />
        </div>
      </CardContent>
    </Card>
  );
}

export function UsagePage() {
  const usageQuery = useUsage();
  const usage = usageQuery.data;

  if (usageQuery.isLoading) return <PageLoader />;

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.22em] text-primaryDark">Usage & Billing</p>
          <h2 className="mt-2 text-3xl font-black tracking-tight text-slate-950">Plan limits and account capacity</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">Monitor search, lead, export, and data retention usage from the backend.</p>
        </div>
        <Badge variant={usage?.account_status === "active" ? "success" : "warning"}>{usage?.account_status || "active"}</Badge>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <UsageMeter title="Searches Today" used={usage?.searches_today} limit={usage?.max_searches_per_day} remaining={usage?.remaining_searches_today} unlimited={usage?.unlimited_searches} icon={TrendingUp} />
        <UsageMeter title="Leads This Month" used={usage?.leads_this_month} limit={usage?.max_leads_per_month} remaining={usage?.remaining_leads_this_month} unlimited={usage?.unlimited_leads} icon={Database} />
        <UsageMeter title="Exports Today" used={usage?.exports_today} limit={usage?.max_exports_per_day} remaining={usage?.remaining_exports_today} unlimited={usage?.unlimited_exports} icon={Download} />
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><WalletCards className="h-5 w-5 text-primaryDark" /> Beta Plan</CardTitle>
            <CardDescription>Current SaaS plan information. Billing integration can be connected later.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-2">
            {[
              ["Beta Access", usage?.beta_access ? "Enabled" : "Disabled"],
              ["Monthly Searches", `${n(usage?.searches_this_month)} / ${n(usage?.max_searches_per_month)}`],
              ["Leads Per Search", n(usage?.max_leads_per_search)],
              ["Monthly Exports", `${n(usage?.exports_this_month)} / ${n(usage?.max_exports_per_month)}`]
            ].map(([label, value]) => (
              <div key={label} className="rounded-2xl border border-borderSoft bg-cardSoft p-4"><p className="text-xs font-bold uppercase tracking-wide text-slate-500">{label}</p><p className="mt-2 text-lg font-black text-slate-950">{value}</p></div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Archive className="h-5 w-5 text-primaryDark" /> Data Retention</CardTitle>
            <CardDescription>Automatic cleanup rules.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {[
              ["Lead retention", `${n(usage?.lead_retention_days)} days`],
              ["Search history", `${n(usage?.search_history_retention_days)} days`],
              ["Raw data", `${n(usage?.raw_data_retention_days)} days`],
              ["Exports", `${n(usage?.export_retention_days)} days`]
            ].map(([label, value]) => <div key={label} className="flex items-center justify-between rounded-2xl border border-borderSoft bg-white/70 p-3"><span className="text-sm font-bold text-slate-700">{label}</span><span className="text-sm font-black text-slate-950">{value}</span></div>)}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="flex flex-col gap-3 p-5 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3"><div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-green-50 text-green-700 ring-1 ring-green-200"><ShieldCheck className="h-5 w-5" /></div><div><p className="font-black text-slate-950">Usage API connected</p><p className="text-sm text-slate-500">This page maps with /api/usage/me/.</p></div></div>
          <div className="inline-flex items-center gap-2 text-sm font-bold text-slate-600"><Activity className="h-4 w-4 text-green-700" /> Auto-refresh enabled</div>
        </CardContent>
      </Card>
    </div>
  );
}
