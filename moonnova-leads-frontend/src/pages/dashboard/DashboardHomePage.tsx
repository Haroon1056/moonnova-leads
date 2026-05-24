import { useQuery } from "@tanstack/react-query";
import {
  ArrowRight,
  Brain,
  CheckCircle2,
  Download,
  Globe2,
  ListChecks,
  Search,
  Sparkles,
  TrendingUp,
  WalletCards
} from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useSearches } from "@/hooks/useSearches";
import { useUsage } from "@/hooks/useUsage";
import { leadService } from "@/services/lead.service";

function number(value?: number | null) {
  return typeof value === "number" ? value.toLocaleString() : "0";
}

function getSearchCount(data: any[]) {
  return data.length;
}

export function DashboardHomePage() {
  const { searchesQuery } = useSearches();
  const usageQuery = useUsage();
  const leadsCountQuery = useQuery({
    queryKey: ["dashboard", "leads-count"],
    queryFn: () => leadService.getLeads({ page: 1, page_size: 1 }),
    refetchInterval: 15000
  });

  const searches = searchesQuery.data || [];
  const usage = usageQuery.data;
  const totalLeads = leadsCountQuery.data?.count || 0;
  const runningSearches = searches.filter((search) => ["pending", "running", "paused"].includes(String(search.status))).length;
  const completedSearches = searches.filter((search) => String(search.status) === "completed").length;

  const stats = [
    { label: "Total Searches", value: number(getSearchCount(searches)), icon: Search, description: `${runningSearches} active right now` },
    { label: "Total Leads", value: number(totalLeads), icon: ListChecks, description: "Collected in your account" },
    { label: "Searches Today", value: number(usage?.searches_today), icon: TrendingUp, description: `${number(usage?.remaining_searches_today)} remaining today` },
    { label: "Exports Today", value: number(usage?.exports_today), icon: Download, description: `${number(usage?.remaining_exports_today)} remaining today` }
  ];

  return (
    <div className="space-y-6">
      <section className="relative overflow-hidden rounded-3xl border border-borderSoft bg-gradient-to-br from-[#181510] via-[#211b12] to-[#0f2926] p-6 text-white shadow-card md:p-8">
        <div className="absolute -right-24 -top-24 h-72 w-72 rounded-full bg-amber-500/20 blur-3xl" />
        <div className="absolute -bottom-24 left-1/3 h-72 w-72 rounded-full bg-teal-500/16 blur-3xl" />
        <div className="relative flex flex-col justify-between gap-6 lg:flex-row lg:items-center">
          <div>
            <Badge className="border-amber-200/20 bg-amber-400/10 text-amber-100">Free Beta Plan</Badge>
            <h2 className="mt-4 max-w-3xl text-3xl font-black tracking-tight md:text-4xl">
              Welcome to MoonNova Leads
            </h2>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-stone-300">
              A focused SaaS workspace to scrape Google Maps style lead data, check website quality, enrich contacts, generate AI insights, and export clean campaign-ready files.
            </p>
            <div className="mt-5 flex flex-wrap gap-3 text-xs font-bold text-stone-300">
              <span className="inline-flex items-center gap-1"><CheckCircle2 className="h-4 w-4 text-emerald-300" /> Backend connected</span>
              <span className="inline-flex items-center gap-1"><CheckCircle2 className="h-4 w-4 text-emerald-300" /> Live status polling</span>
              <span className="inline-flex items-center gap-1"><CheckCircle2 className="h-4 w-4 text-emerald-300" /> Export workflow ready</span>
            </div>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row lg:flex-col">
            <Link to="/dashboard/searches"><Button size="lg" className="w-full"><Search className="mr-2 h-4 w-4" />Start Search</Button></Link>
            <Link to="/dashboard/leads"><Button size="lg" variant="outline" className="w-full border-white/15 bg-white/10 text-white hover:bg-white/15 hover:text-white"><ListChecks className="mr-2 h-4 w-4" />View Leads</Button></Link>
          </div>
        </div>
      </section>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.label}>
              <CardContent className="flex items-center justify-between p-5">
                <div>
                  <p className="text-sm font-bold text-slate-500">{stat.label}</p>
                  <p className="mt-2 text-3xl font-black text-slate-950">{stat.value}</p>
                  <p className="mt-1 text-xs font-medium text-slate-500">{stat.description}</p>
                </div>
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primarySoft text-primaryDark ring-1 ring-orange-200">
                  <Icon className="h-5 w-5" />
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle>Workflow Pipeline</CardTitle>
            <CardDescription>Every workspace page is arranged around this simple production flow.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 md:grid-cols-4">
              {[
                { label: "Search", text: "Keyword + location jobs", icon: Search, href: "/dashboard/searches" },
                { label: "Review", text: "Filter and qualify leads", icon: ListChecks, href: "/dashboard/leads" },
                { label: "AI", text: "Generate insights", icon: Brain, href: "/dashboard/ai" },
                { label: "Export", text: "Download clean files", icon: Download, href: "/dashboard/exports" }
              ].map((item) => {
                const Icon = item.icon;
                return (
                  <Link key={item.label} to={item.href} className="rounded-2xl border border-borderSoft bg-cardSoft p-4 transition hover:-translate-y-0.5 hover:bg-white hover:shadow-soft">
                    <Icon className="h-6 w-6 text-primaryDark" />
                    <p className="mt-3 text-sm font-black text-slate-900">{item.label}</p>
                    <p className="mt-1 text-xs leading-5 text-slate-500">{item.text}</p>
                  </Link>
                );
              })}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Account Snapshot</CardTitle>
            <CardDescription>Backend usage and current account limits.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {[
              ["Account", usage?.account_status || "active", WalletCards],
              ["Completed searches", String(completedSearches), CheckCircle2],
              ["Monthly leads", number(usage?.leads_this_month), Globe2],
              ["AI workspace", "Ready", Sparkles]
            ].map(([label, value, Icon]: any) => (
              <div key={label} className="flex items-center justify-between rounded-2xl border border-borderSoft bg-white/70 p-3">
                <div className="flex items-center gap-3">
                  <Icon className="h-4 w-4 text-primaryDark" />
                  <span className="text-sm font-bold text-slate-700">{label}</span>
                </div>
                <span className="text-sm font-black text-slate-950">{value}</span>
              </div>
            ))}
            <Link to="/dashboard/usage"><Button variant="outline" className="w-full">View Usage <ArrowRight className="ml-2 h-4 w-4" /></Button></Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
