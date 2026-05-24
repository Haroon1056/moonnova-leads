import {
  AlertTriangle,
  ArrowLeft,
  Brain,
  CheckCircle2,
  Download,
  ExternalLink,
  Globe,
  Loader2,
  Mail,
  MailCheck,
  MapPin,
  Pause,
  Phone,
  Play,
  Square,
  Star,
  Wifi,
  WifiOff
} from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card";
import { useRealtime } from "@/hooks/useRealtime";
import { useSearchDetail } from "@/hooks/useSearches";
import { useSearchEnrichment } from "@/hooks/useEnrichment";
import { useRealtimeStore } from "@/store/realtimeStore";
import { cn, formatDate } from "@/lib/utils";
import type { Lead } from "@/types/lead";

function getStatusVariant(status?: string) {
  if (status === "completed") return "success";
  if (status === "failed" || status === "cancelled") return "danger";
  if (status === "running") return "default";
  if (status === "paused") return "warning";
  return "neutral";
}

function getWebsiteBadgeVariant(status?: string | null) {
  if (!status || status === "unknown") return "neutral";
  if (status === "working") return "success";
  if (status === "no_website") return "warning";

  if (
    status === "broken" ||
    status === "404" ||
    status === "expired_domain" ||
    status === "redirect_error" ||
    status === "timeout" ||
    status === "ssl_error" ||
    status === "connection_error" ||
    status === "invalid_url" ||
    status === "protected"
  ) {
    return "danger";
  }

  if (status === "social_only" || status === "free_builder") return "warning";

  return "neutral";
}

function formatWebsiteStatus(status?: string | null) {
  if (!status) return "Unknown";

  return status
    .replaceAll("_", " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function getProgress(search: any, realtimeProgress: any) {
  if (typeof realtimeProgress?.progress === "number") {
    return realtimeProgress.progress;
  }

  if (typeof search?.progress === "number") {
    return search.progress;
  }

  const totalTasks = search?.total_tasks || 0;
  const completedTasks = search?.completed_tasks || 0;
  const failedTasks = search?.failed_tasks || 0;

  if (totalTasks) {
    return Math.min(
      100,
      Math.round(((completedTasks + failedTasks) / totalTasks) * 100)
    );
  }

  if (search?.status === "completed") return 100;

  return 0;
}

function getLeadName(lead: Lead) {
  return lead.name || lead.business_name || "Unnamed Business";
}

function getLeadEmail(lead: Lead) {
  return lead.email_1 || lead.email || lead.email_2 || lead.email_3 || null;
}

function getLeadLocation(lead: Lead) {
  const parts = [lead.city, lead.state, lead.country].filter(Boolean);

  if (parts.length > 0) return parts.join(", ");

  return lead.location || lead.address || "-";
}

function getScoreVariant(score?: number | null) {
  if (!score) return "neutral";
  if (score >= 75) return "success";
  if (score >= 45) return "warning";
  return "neutral";
}

function getSearchKeywordText(search: any) {
  if (Array.isArray(search.keywords) && search.keywords.length > 0) {
    return search.keywords.join(", ");
  }

  if (search.query_tasks?.length) {
    const keywords = Array.from(
      new Set(search.query_tasks.map((task: any) => task.keyword).filter(Boolean))
    );

    return keywords.join(", ");
  }

  return search.keyword || "-";
}

function getSearchLocationText(search: any) {
  if (Array.isArray(search.locations) && search.locations.length > 0) {
    return search.locations.join(", ");
  }

  if (search.query_tasks?.length) {
    const locations = Array.from(
      new Set(search.query_tasks.map((task: any) => task.location).filter(Boolean))
    );

    return locations.join(", ");
  }

  return search.location || "-";
}

export function SearchDetailPage() {
  useRealtime();

  const params = useParams();
  const searchId = params.id as string;

  const {
    searchQuery,
    searchLeadsQuery,
    pauseMutation,
    resumeMutation,
    cancelMutation
  } = useSearchDetail(searchId);

  const { enrichmentJobQuery, startEnrichmentMutation } =
    useSearchEnrichment(searchId);

  const { connected, liveLeads, searchProgress } = useRealtimeStore();

  const search = searchQuery.data;
  const enrichmentJob = enrichmentJobQuery.data;

  const realtimeProgress = searchProgress[Number(searchId)];
  const progress = getProgress(search, realtimeProgress);

  const backendLeads = searchLeadsQuery.data || [];

  const filteredLiveLeads = liveLeads.filter(
    (lead) => Number(lead.search) === Number(searchId)
  );

  const leads = [...filteredLiveLeads, ...backendLeads]
    .filter((lead) => Number(lead.search) === Number(searchId))
    .filter(
      (lead, index, array) =>
        array.findIndex((item) => item.id === lead.id) === index
    );

  const noWebsiteCount = leads.filter(
    (lead) => lead.website_status === "no_website" || lead.has_website === false
  ).length;

  const brokenWebsiteCount = leads.filter(
    (lead) =>
      lead.is_broken_website ||
      [
        "broken",
        "404",
        "expired_domain",
        "redirect_error",
        "timeout",
        "ssl_error",
        "connection_error",
        "invalid_url",
        "protected"
      ].includes(String(lead.website_status))
  ).length;

  const emailsFoundCount = leads.filter((lead) => Boolean(getLeadEmail(lead)))
    .length;

  if (searchQuery.isLoading) {
    return (
      <div className="flex min-h-[300px] items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
      </div>
    );
  }

  if (searchQuery.isError || !search) {
    return (
      <Card>
        <CardContent className="p-10 text-center">
          <AlertTriangle className="mx-auto h-10 w-10 text-amber-500" />
          <h3 className="mt-3 text-lg font-semibold">Search not found</h3>
          <p className="mt-1 text-sm text-slate-500">
            This search could not be loaded.
          </p>
          <Link to="/dashboard/searches">
            <Button className="mt-5">Back to Searches</Button>
          </Link>
        </CardContent>
      </Card>
    );
  }

  const isRunning =
    search.status === "running" ||
    search.status === "pending" ||
    search.status === "queued";

  const isPaused = search.status === "paused";

  const enrichmentRunning =
    enrichmentJob?.status === "pending" || enrichmentJob?.status === "running";

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-start">
        <div>
          <Link
            to="/dashboard/searches"
            className="mb-3 inline-flex items-center text-sm font-medium text-slate-500 hover:text-slate-900"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Searches
          </Link>

          <div className="flex flex-wrap items-center gap-3">
            <h2 className="text-2xl font-bold text-slate-950">
              Search #{search.id}
            </h2>

            <Badge variant={getStatusVariant(search.status)}>
              Scraping: {search.status}
            </Badge>

            <Badge variant={connected ? "success" : "neutral"}>
              {connected ? (
                <Wifi className="mr-1 h-3 w-3" />
              ) : (
                <WifiOff className="mr-1 h-3 w-3" />
              )}
              {connected ? "Realtime Connected" : "Realtime Offline"}
            </Badge>
          </div>

          <p className="mt-2 text-sm text-slate-500">
            Created {formatDate(search.created_at)}
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <Link to={`/dashboard/ai?search_id=${search.id}`}>
            <Button variant="outline">
              <Brain className="mr-2 h-4 w-4" />
              Open AI Workspace
            </Button>
          </Link>

          <Link to={`/dashboard/exports?search_id=${search.id}`}>
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              Export Leads
            </Button>
          </Link>
          
          {isRunning && (
            <Button
              variant="outline"
              onClick={() => pauseMutation.mutate()}
              disabled={pauseMutation.isPending}
            >
              <Pause className="mr-2 h-4 w-4" />
              Pause
            </Button>
          )}

          {isPaused && (
            <Button
              variant="outline"
              onClick={() => resumeMutation.mutate()}
              disabled={resumeMutation.isPending}
            >
              <Play className="mr-2 h-4 w-4" />
              Resume
            </Button>
          )}

          {(isRunning || isPaused) && (
            <Button
              variant="danger"
              onClick={() => cancelMutation.mutate()}
              disabled={cancelMutation.isPending}
            >
              <Square className="mr-2 h-4 w-4" />
              Cancel
            </Button>
          )}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-6">
        <Card>
          <CardContent className="p-5">
            <p className="text-sm text-slate-500">Scraping</p>
            <p className="mt-2 text-3xl font-bold">{progress}%</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <p className="text-sm text-slate-500">Total Leads</p>
            <p className="mt-2 text-3xl font-bold">{leads.length}</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <p className="text-sm text-slate-500">Emails Found</p>
            <p className="mt-2 text-3xl font-bold">{emailsFoundCount}</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <p className="text-sm text-slate-500">No Website</p>
            <p className="mt-2 text-3xl font-bold">{noWebsiteCount}</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <p className="text-sm text-slate-500">Broken Sites</p>
            <p className="mt-2 text-3xl font-bold">{brokenWebsiteCount}</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <p className="text-sm text-slate-500">Enrichment</p>
            <p className="mt-2 text-2xl font-bold capitalize">
              {search.email_enrichment
                ? enrichmentJob?.status || "Waiting"
                : "Off"}
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Scraping Progress</CardTitle>
          <CardDescription>
            Scraping collects Google Maps business leads. Enrichment is separate.
          </CardDescription>
        </CardHeader>

        <CardContent>
          <div className="h-3 overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full bg-primary transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>

          <div className="mt-4 grid gap-4 md:grid-cols-3">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm font-medium text-slate-700">Keywords</p>
              <p className="mt-1 text-sm text-slate-500">
                {getSearchKeywordText(search)}
              </p>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm font-medium text-slate-700">Locations</p>
              <p className="mt-1 text-sm text-slate-500">
                {getSearchLocationText(search)}
              </p>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm font-medium text-slate-700">Tasks</p>
              <p className="mt-1 text-sm text-slate-500">
                {search.completed_tasks || 0} completed /{" "}
                {search.total_tasks || 0} total
              </p>
            </div>
          </div>

          {search.error_message && (
            <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              {search.error_message}
            </div>
          )}

          {search.status === "completed" && (
            <div className="mt-4 flex items-center gap-2 rounded-2xl border border-green-200 bg-green-50 p-4 text-sm text-green-700">
              <CheckCircle2 className="h-4 w-4" />
              Scraping completed successfully.
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <MailCheck className="h-5 w-5 text-primary" />
              Enrichment Status
            </CardTitle>
            <CardDescription>
              Website checking and email discovery run after scraping.
            </CardDescription>
          </div>

          {!search.email_enrichment && (
            <Badge variant="neutral">Disabled for this search</Badge>
          )}

          {search.email_enrichment && enrichmentJob?.status && (
            <Badge variant={getStatusVariant(enrichmentJob.status)}>
              {enrichmentJob.status}
            </Badge>
          )}

          {search.email_enrichment && !enrichmentJob && (
            <Badge variant="warning">Waiting</Badge>
          )}
        </CardHeader>

        <CardContent>
          {!search.email_enrichment ? (
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
              Enrichment was turned off before starting this search. The system
              will only scrape business leads and will not check websites or
              extract emails automatically.
            </div>
          ) : enrichmentJob ? (
            <div className="space-y-4">
              <div className="h-3 overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-primary transition-all"
                  style={{ width: `${enrichmentJob.progress || 0}%` }}
                />
              </div>

              <div className="grid gap-4 md:grid-cols-4">
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-xs text-slate-500">Progress</p>
                  <p className="mt-1 text-xl font-bold">
                    {enrichmentJob.progress || 0}%
                  </p>
                </div>

                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-xs text-slate-500">Total</p>
                  <p className="mt-1 text-xl font-bold">
                    {enrichmentJob.total_items}
                  </p>
                </div>

                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-xs text-slate-500">Completed</p>
                  <p className="mt-1 text-xl font-bold">
                    {enrichmentJob.completed_items}
                  </p>
                </div>

                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-xs text-slate-500">Failed / Skipped</p>
                  <p className="mt-1 text-xl font-bold">
                    {enrichmentJob.failed_items + enrichmentJob.skipped_items}
                  </p>
                </div>
              </div>

              {enrichmentRunning && (
                <div className="rounded-2xl border border-indigo-200 bg-indigo-50 p-4 text-sm text-indigo-700">
                  Enrichment is running in the background. You can start another
                  search because scraping and enrichment are now separated.
                </div>
              )}

              {enrichmentJob.status === "completed" && (
                <div className="rounded-2xl border border-green-200 bg-green-50 p-4 text-sm text-green-700">
                  Enrichment completed. Website status and emails are now updated.
                </div>
              )}
            </div>
          ) : search.status === "completed" ? (
            <div className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="text-sm font-medium text-slate-800">
                  Enrichment has not started yet.
                </p>
                <p className="mt-1 text-sm text-slate-500">
                  If it does not start automatically, you can start it manually.
                </p>
              </div>

              <Button
                onClick={() => startEnrichmentMutation.mutate()}
                disabled={startEnrichmentMutation.isPending}
              >
                {startEnrichmentMutation.isPending && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                Start Enrichment
              </Button>
            </div>
          ) : (
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
              Enrichment will start after scraping is completed.
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <CardTitle>Search Leads</CardTitle>
            <CardDescription>
              Showing only leads from this search ID.
            </CardDescription>
          </div>

          <div className="text-sm text-slate-500">
            Showing{" "}
            <span className="font-semibold text-slate-900">{leads.length}</span>{" "}
            leads
          </div>
        </CardHeader>

        <CardContent>
          {searchLeadsQuery.isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((item) => (
                <div
                  key={item}
                  className="h-16 animate-pulse rounded-2xl bg-slate-100"
                />
              ))}
            </div>
          ) : leads.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-10 text-center">
              <Loader2
                className={cn(
                  "mx-auto h-8 w-8 text-slate-400",
                  isRunning && "animate-spin"
                )}
              />
              <h3 className="mt-3 font-semibold text-slate-800">
                Waiting for leads
              </h3>
              <p className="mt-1 text-sm text-slate-500">
                Only leads from this search will appear here.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto rounded-2xl border border-slate-200">
              <table className="min-w-[1500px] w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                  <tr>
                    <th className="sticky left-0 z-10 bg-slate-50 px-4 py-3">
                      Business
                    </th>
                    <th className="px-4 py-3">Keyword</th>
                    <th className="px-4 py-3">Category</th>
                    <th className="px-4 py-3">Location</th>
                    <th className="px-4 py-3">Phone</th>
                    <th className="px-4 py-3">Email</th>
                    <th className="px-4 py-3">Website</th>
                    <th className="px-4 py-3">Website Status</th>
                    <th className="px-4 py-3">Platform</th>
                    <th className="px-4 py-3">Rating</th>
                    <th className="px-4 py-3">Reviews</th>
                    <th className="px-4 py-3">Lead Score</th>
                    <th className="px-4 py-3">Opportunity</th>
                    <th className="px-4 py-3">Enrichment</th>
                    <th className="px-4 py-3">Source</th>
                    <th className="px-4 py-3">Map</th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-slate-200 bg-white">
                  {leads.map((lead) => {
                    const email = getLeadEmail(lead);
                    const website = lead.website || lead.website_url;
                    const websiteStatus = lead.website_status || "unknown";

                    return (
                      <tr key={lead.id} className="hover:bg-slate-50">
                        <td className="sticky left-0 z-10 bg-white px-4 py-4 align-top">
                          <div className="max-w-[260px]">
                            <div className="font-semibold text-slate-900">
                              {getLeadName(lead)}
                            </div>

                            <div className="mt-1 flex items-center gap-1 text-xs text-slate-500">
                              <MapPin className="h-3 w-3" />
                              <span className="truncate">
                                {lead.address || getLeadLocation(lead)}
                              </span>
                            </div>

                            {lead.is_favorite && (
                              <Badge variant="warning" className="mt-2">
                                <Star className="mr-1 h-3 w-3" />
                                Favorite
                              </Badge>
                            )}
                          </div>
                        </td>

                        <td className="px-4 py-4 align-top text-slate-600">
                          {lead.keyword || lead.source_keyword || "-"}
                        </td>

                        <td className="px-4 py-4 align-top text-slate-600">
                          {lead.category || "-"}
                        </td>

                        <td className="px-4 py-4 align-top text-slate-600">
                          {getLeadLocation(lead)}
                        </td>

                        <td className="px-4 py-4 align-top">
                          {lead.phone ? (
                            <a
                              href={`tel:${lead.phone}`}
                              className="inline-flex items-center text-primary hover:underline"
                            >
                              <Phone className="mr-1 h-3 w-3" />
                              {lead.phone}
                            </a>
                          ) : (
                            <span className="text-slate-400">-</span>
                          )}
                        </td>

                        <td className="px-4 py-4 align-top">
                          {email ? (
                            <a
                              href={`mailto:${email}`}
                              className="inline-flex items-center text-primary hover:underline"
                            >
                              <Mail className="mr-1 h-3 w-3" />
                              {email}
                            </a>
                          ) : (
                            <Badge variant="neutral">No Email</Badge>
                          )}

                          {lead.email_confidence ? (
                            <div className="mt-1 text-xs text-slate-500">
                              Confidence: {lead.email_confidence}%
                            </div>
                          ) : null}
                        </td>

                        <td className="px-4 py-4 align-top">
                          {website ? (
                            <a
                              href={website}
                              target="_blank"
                              rel="noreferrer"
                              className="inline-flex max-w-[180px] items-center truncate text-primary hover:underline"
                            >
                              <Globe className="mr-1 h-3 w-3 shrink-0" />
                              <span className="truncate">
                                {lead.domain || website}
                              </span>
                            </a>
                          ) : (
                            <Badge variant="warning">No Website</Badge>
                          )}
                        </td>

                        <td className="px-4 py-4 align-top">
                          <Badge variant={getWebsiteBadgeVariant(websiteStatus)}>
                            {formatWebsiteStatus(websiteStatus)}
                          </Badge>

                          {lead.website_http_status ? (
                            <div className="mt-1 text-xs text-slate-500">
                              HTTP {lead.website_http_status}
                            </div>
                          ) : null}

                          {lead.is_social_only && (
                            <div className="mt-1">
                              <Badge variant="warning">Social Only</Badge>
                            </div>
                          )}

                          {lead.is_free_builder && (
                            <div className="mt-1">
                              <Badge variant="warning">Free Builder</Badge>
                            </div>
                          )}
                        </td>

                        <td className="px-4 py-4 align-top text-slate-600">
                          {lead.website_platform || "-"}
                        </td>

                        <td className="px-4 py-4 align-top">
                          <div className="font-medium text-slate-800">
                            {lead.rating || "-"}
                          </div>
                        </td>

                        <td className="px-4 py-4 align-top text-slate-600">
                          {lead.review_count || lead.rating_count || "-"}
                        </td>

                        <td className="px-4 py-4 align-top">
                          <Badge variant={getScoreVariant(lead.lead_score)}>
                            {lead.lead_score ?? 0}
                          </Badge>
                        </td>

                        <td className="px-4 py-4 align-top">
                          <Badge variant={getScoreVariant(lead.opportunity_score)}>
                            {lead.opportunity_score ?? 0}
                          </Badge>

                          {lead.opportunity_reason && (
                            <div className="mt-1 max-w-[220px] text-xs text-slate-500">
                              {lead.opportunity_reason}
                            </div>
                          )}
                        </td>

                        <td className="px-4 py-4 align-top">
                          <Badge variant="neutral">
                            {lead.enrichment_status || "not_started"}
                          </Badge>
                        </td>

                        <td className="px-4 py-4 align-top text-slate-600">
                          <div className="max-w-[220px]">
                            <div>
                              {lead.source_query ||
                                `${lead.source_keyword || lead.keyword || "-"} in ${
                                  lead.source_location || lead.location || "-"
                                }`}
                            </div>
                            <div className="mt-1 text-xs text-slate-400">
                              Added {formatDate(lead.created_at)}
                            </div>
                          </div>
                        </td>

                        <td className="px-4 py-4 align-top">
                          {lead.map_link ? (
                            <a
                              href={lead.map_link}
                              target="_blank"
                              rel="noreferrer"
                              className="inline-flex items-center text-primary hover:underline"
                            >
                              Open
                              <ExternalLink className="ml-1 h-3 w-3" />
                            </a>
                          ) : (
                            <span className="text-slate-400">-</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}