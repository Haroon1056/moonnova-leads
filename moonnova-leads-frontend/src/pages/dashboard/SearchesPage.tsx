import { zodResolver } from "@hookform/resolvers/zod";
import {
  ArrowRight,
  CheckCircle2,
  Clock,
  Loader2,
  MapPin,
  Play,
  Search,
  XCircle
} from "lucide-react";
import { useMemo } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { z } from "zod";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { TableSkeleton } from "@/components/ui/loading";
import { useSearches } from "@/hooks/useSearches";
import { formatDate } from "@/lib/utils";
import type { SearchJob, ScrapeMode } from "@/types/search";

const formSchema = z.object({
  keywords: z.string().min(2, "Add at least one keyword"),
  locations: z.string().min(2, "Add at least one location"),
  max_leads: z.number().min(1).max(5000),
  scrape_mode: z.enum(["safe", "balanced", "deep"]),
  email_enrichment: z.boolean()
});

type FormValues = z.infer<typeof formSchema>;

function splitLines(value: string) {
  return value
    .replace(/\r/g, "")
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function getSearchTitle(search: SearchJob) {
  const keywords = search.keywords?.join(", ") || search.keyword || "Search";
  const locations = search.locations?.join(", ") || search.location || "Location";

  return `${keywords} in ${locations}`;
}

function statusVariant(status?: string) {
  if (status === "completed") return "success";
  if (status === "failed" || status === "cancelled") return "danger";
  if (status === "running") return "default";

  return "warning";
}

function statusIcon(status?: string) {
  if (status === "completed") return CheckCircle2;
  if (status === "failed" || status === "cancelled") return XCircle;

  return Clock;
}

function getProgress(search: SearchJob) {
  if (typeof search.progress === "number") {
    return Math.min(100, Math.max(0, search.progress));
  }

  if (search.total_tasks) {
    return Math.round(((search.completed_tasks || 0) / search.total_tasks) * 100);
  }

  return 0;
}

function getLeadsCount(search: SearchJob) {
  return search.leads_count_db || search.leads_count || 0;
}

const presets = [
  {
    name: "AU Web Design Leads",
    keywords: "plumber\nelectrician\nroofer",
    locations: "Perth WA\nSydney NSW\nBrisbane QLD"
  },
  {
    name: "No Website Targets",
    keywords: "cleaning service\nconstruction company\ngym",
    locations: "Melbourne VIC\nAdelaide SA\nGold Coast QLD"
  },
  {
    name: "Solar Opportunities",
    keywords: "warehouse\nfarm\nfactory",
    locations: "Karachi\nLahore\nIslamabad"
  }
];

export function SearchesPage() {
  const navigate = useNavigate();
  const { searchesQuery, createSearchMutation } = useSearches();

  const searches = searchesQuery.data || [];

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      keywords: "",
      locations: "",
      max_leads: 100,
      scrape_mode: "balanced",
      email_enrichment: true
    }
  });

  const keywords = splitLines(form.watch("keywords") || "");
  const locations = splitLines(form.watch("locations") || "");
  const taskCount = keywords.length * locations.length;

  const summary = useMemo(
    () => ({
      total: searches.length,
      active: searches.filter((search) =>
        ["pending", "running", "paused"].includes(String(search.status))
      ).length,
      completed: searches.filter((search) => String(search.status) === "completed")
        .length,
      failed: searches.filter((search) =>
        ["failed", "cancelled"].includes(String(search.status))
      ).length
    }),
    [searches]
  );

  async function onSubmit(values: FormValues) {
    const search = await createSearchMutation.mutateAsync({
      keywords: splitLines(values.keywords),
      locations: splitLines(values.locations),
      max_leads: values.max_leads,
      scrape_mode: values.scrape_mode as ScrapeMode,
      email_enrichment: values.email_enrichment
    });

    if (search?.id) {
      navigate(`/dashboard/searches/${search.id}`);
    }
  }

  return (
    <div className="space-y-6 overflow-x-hidden">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div className="min-w-0">
          <p className="text-xs font-black uppercase tracking-[0.22em] text-primaryDark">
            Search Operations
          </p>
          <h2 className="mt-2 text-3xl font-black tracking-tight text-slate-950">
            Create and monitor scraping jobs
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
            Create one job from multiple keywords and locations. Enrichment is optional
            and runs after scraping.
          </p>
        </div>

        <div className="grid grid-cols-4 gap-2 rounded-2xl border border-borderSoft bg-white/75 p-2 shadow-sm">
          {[
            ["Total", summary.total],
            ["Active", summary.active],
            ["Done", summary.completed],
            ["Issues", summary.failed]
          ].map(([label, value]) => (
            <div key={label} className="px-3 py-2 text-center">
              <div className="text-lg font-black text-slate-950">{value}</div>
              <div className="text-[10px] font-bold uppercase tracking-wide text-slate-500">
                {label}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid min-w-0 gap-6 xl:grid-cols-[420px_minmax(0,1fr)]">
        <Card className="min-w-0">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="h-5 w-5 text-primaryDark" />
              Start New Search
            </CardTitle>
            <CardDescription>
              Use clean inputs. One keyword/location per line is easiest.
            </CardDescription>
          </CardHeader>

          <CardContent>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <div>
                <Label>Keywords</Label>
                <textarea
                  className="min-h-28 w-full resize-y rounded-2xl border border-borderSoft bg-white/85 p-3 text-sm outline-none placeholder:text-slate-400 focus:border-primary focus:ring-2 focus:ring-primary/20"
                  placeholder={"plumber\nelectrician\nroofing contractor"}
                  {...form.register("keywords")}
                />
                <p className="mt-1 text-xs text-slate-500">
                  Add one keyword per line, or separate with commas.
                </p>
                {form.formState.errors.keywords && (
                  <p className="mt-1 text-xs text-red-600">
                    {form.formState.errors.keywords.message}
                  </p>
                )}
              </div>

              <div>
                <Label>Locations</Label>
                <textarea
                  className="min-h-28 w-full resize-y rounded-2xl border border-borderSoft bg-white/85 p-3 text-sm outline-none placeholder:text-slate-400 focus:border-primary focus:ring-2 focus:ring-primary/20"
                  placeholder={"Perth WA\nSydney NSW\nBrisbane QLD"}
                  {...form.register("locations")}
                />
                <p className="mt-1 text-xs text-slate-500">
                  Add one city, suburb, state, or postcode per line.
                </p>
                {form.formState.errors.locations && (
                  <p className="mt-1 text-xs text-red-600">
                    {form.formState.errors.locations.message}
                  </p>
                )}
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <Label>Max leads / task</Label>
                  <Input
                    type="number"
                    min={1}
                    max={5000}
                    {...form.register("max_leads", { valueAsNumber: true })}
                  />
                </div>

                <div>
                  <Label>Scrape Mode</Label>
                  <select
                    className="h-11 w-full rounded-xl border border-borderSoft bg-white/85 px-3 text-sm"
                    {...form.register("scrape_mode")}
                  >
                    <option value="safe">Safe</option>
                    <option value="balanced">Balanced</option>
                    <option value="deep">Deep</option>
                  </select>
                </div>
              </div>

              <label className="flex items-start gap-3 rounded-2xl border border-borderSoft bg-cardSoft p-3">
                <input
                  type="checkbox"
                  className="mt-1 h-4 w-4 accent-amber-700"
                  {...form.register("email_enrichment")}
                />
                <span>
                  <span className="block text-sm font-bold text-slate-800">
                    Run website/email enrichment after scraping
                  </span>
                  <span className="text-xs leading-5 text-slate-500">
                    Recommended for export-ready lead files.
                  </span>
                </span>
              </label>

              <div className="grid grid-cols-3 gap-2 rounded-2xl border border-borderSoft bg-white/70 p-3 text-center">
                <div>
                  <div className="text-xl font-black">{keywords.length}</div>
                  <div className="text-[10px] font-bold uppercase text-slate-500">
                    Keywords
                  </div>
                </div>

                <div>
                  <div className="text-xl font-black">{locations.length}</div>
                  <div className="text-[10px] font-bold uppercase text-slate-500">
                    Locations
                  </div>
                </div>

                <div>
                  <div className="text-xl font-black">{taskCount}</div>
                  <div className="text-[10px] font-bold uppercase text-slate-500">
                    Tasks
                  </div>
                </div>
              </div>

              <Button
                type="submit"
                className="w-full"
                disabled={createSearchMutation.isPending}
              >
                {createSearchMutation.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Play className="mr-2 h-4 w-4" />
                )}
                Start Search
              </Button>
            </form>

            <div className="mt-5 space-y-2">
              <div className="text-xs font-black uppercase tracking-wide text-slate-500">
                Quick Templates
              </div>

              {presets.map((preset) => (
                <button
                  key={preset.name}
                  type="button"
                  className="w-full rounded-2xl border border-borderSoft bg-white/70 p-3 text-left transition hover:border-primary/40 hover:bg-primarySoft"
                  onClick={() =>
                    form.reset({
                      ...form.getValues(),
                      keywords: preset.keywords,
                      locations: preset.locations
                    })
                  }
                >
                  <div className="text-sm font-bold text-slate-900">
                    {preset.name}
                  </div>
                  <div className="mt-1 text-xs text-slate-500">
                    Apply keyword and location sample
                  </div>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="min-w-0">
          <CardHeader className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <CardTitle>Recent Searches</CardTitle>
              <CardDescription>
                Open a search to see live progress, leads, and enrichment status.
              </CardDescription>
            </div>

            {/* <Button variant="outline">
              <SlidersHorizontal className="mr-2 h-4 w-4" />
              Filters
            </Button> */}
          </CardHeader>

          <CardContent>
            <div className="table-shell search-table-shell">
              <div className="table-scroll premium-table-scroll">
                {searchesQuery.isLoading ? (
                  <TableSkeleton />
                ) : searches.length === 0 ? (
                  <div className="flex min-h-72 flex-col items-center justify-center p-8 text-center">
                    <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primarySoft text-primaryDark">
                      <Search className="h-7 w-7" />
                    </div>
                    <h3 className="mt-4 text-lg font-black text-slate-950">
                      No searches yet
                    </h3>
                    <p className="mt-2 max-w-md text-sm leading-6 text-slate-500">
                      Create your first scraping job to start collecting leads.
                    </p>
                  </div>
                ) : (
                  <table className="data-table searches-data-table">
                    <thead>
                      <tr>
                        <th>Search</th>
                        <th>Status</th>
                        <th>Progress</th>
                        <th>Leads</th>
                        <th>Created</th>
                        <th className="text-right">Action</th>
                      </tr>
                    </thead>

                    <tbody>
                      {searches.map((search) => {
                        const Icon = statusIcon(String(search.status));
                        const progress = getProgress(search);
                        const leadsCount = getLeadsCount(search);

                        return (
                          <tr key={search.id}>
                            <td>
                              <div className="max-w-[360px]">
                                <div className="line-clamp-2 font-black leading-5 text-slate-900">
                                  {getSearchTitle(search)}
                                </div>
                                <div className="mt-2 flex flex-wrap items-center gap-2 text-xs font-medium text-slate-500">
                                  <span className="inline-flex items-center gap-1">
                                    <MapPin className="h-3.5 w-3.5" />
                                    {search.scrape_mode || "safe"} mode
                                  </span>
                                  <span>•</span>
                                  <span>
                                    {search.email_enrichment
                                      ? "Enrichment enabled"
                                      : "Enrichment disabled"}
                                  </span>
                                </div>
                              </div>
                            </td>

                            <td>
                              <Badge variant={statusVariant(String(search.status))}>
                                <Icon className="mr-1 h-3.5 w-3.5" />
                                {search.status}
                              </Badge>
                            </td>

                            <td>
                              <div className="min-w-[150px]">
                                <div className="h-2 rounded-full bg-stone-100">
                                  <div
                                    className="h-2 rounded-full bg-gradient-to-r from-amber-600 to-teal-700"
                                    style={{ width: `${progress}%` }}
                                  />
                                </div>
                                <div className="mt-1 text-xs font-bold text-slate-500">
                                  {progress}%
                                </div>
                              </div>
                            </td>

                            <td>
                              <span className="text-base font-black text-slate-950">
                                {leadsCount}
                              </span>
                            </td>

                            <td className="whitespace-nowrap text-slate-500">
                              {formatDate(search.created_at)}
                            </td>

                            <td className="text-right">
                              <Link
                                to={`/dashboard/searches/${search.id}`}
                                className="inline-flex justify-end"
                              >
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="inline-flex min-w-[92px] items-center justify-center whitespace-nowrap rounded-xl px-4"
                                >
                                  Open
                                  <ArrowRight className="ml-2 h-3.5 w-3.5 shrink-0" />
                                </Button>
                              </Link>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}