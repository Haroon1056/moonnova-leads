import {
  Brain,
  CheckCircle2,
  Clock,
  Download,
  Eye,
  Loader2,
  RefreshCw,
  Search,
  Sparkles,
  WalletCards,
  XCircle
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

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

import { AiInsightDrawer } from "@/components/ai/AiInsightDrawer";

import { useAiJobs, useAiUsage, useBulkAiGeneration } from "@/hooks/useAI";
import { useSearches } from "@/hooks/useSearches";

import { searchService } from "@/services/search.service";

import { formatDate } from "@/lib/utils";

import type { AiJob } from "@/types/ai";
import type { SearchJob } from "@/types/search";
import type { Lead } from "@/types/lead";

function getLeadName(lead: Lead) {
  return lead.name || lead.business_name || "Unnamed Business";
}

function getLeadEmail(lead: Lead) {
  return lead.email_1 || lead.email || lead.email_2 || lead.email_3 || "";
}

function getWebsite(lead: Lead) {
  return lead.website || lead.website_url || "";
}

function getStatusVariant(status?: string) {
  if (status === "completed") return "success";
  if (status === "failed" || status === "cancelled") return "danger";
  if (status === "running") return "default";
  if (status === "pending") return "warning";
  return "neutral";
}

function getStatusIcon(status?: string) {
  if (status === "completed") return CheckCircle2;
  if (status === "failed" || status === "cancelled") return XCircle;
  if (status === "running") return RefreshCw;
  return Clock;
}

function getProcessedItems(job: AiJob) {
  return (
    (job.completed_items || 0) +
    (job.failed_items || 0) +
    (job.skipped_items || 0)
  );
}

function getDisplayStatus(job: AiJob) {
  const processed = getProcessedItems(job);

  if (
    job.total_items &&
    processed >= job.total_items &&
    job.status !== "failed" &&
    job.status !== "cancelled"
  ) {
    return "completed";
  }

  return job.status;
}

function getProgress(job: AiJob) {
  if (typeof job.progress === "number") return job.progress;

  if (!job.total_items) return 0;

  return Math.min(
    100,
    Math.round((getProcessedItems(job) / job.total_items) * 100)
  );
}

function getSearchTitle(search: SearchJob) {
  const keywords = search.keywords?.join(", ") || search.keyword || "Search";
  const locations =
    search.locations?.join(", ") || search.location || "Location";

  return `${keywords} in ${locations}`;
}

function getLeadIds(leads: Lead[]) {
  return leads
    .map((lead) => Number(lead.id))
    .filter((id) => Number.isFinite(id) && id > 0);
}

function downloadCsv(filename: string, leads: Lead[]) {
  const headers = [
    "Business Name",
    "Category",
    "Keyword",
    "Location",
    "Phone",
    "Email",
    "Website",
    "Website Status",
    "Rating",
    "Reviews",
    "Lead Score",
    "AI Priority"
  ];

  const rows = leads.map((lead) => [
    getLeadName(lead),
    lead.category || "",
    lead.keyword || lead.source_keyword || "",
    lead.location || lead.source_location || "",
    lead.phone || "",
    getLeadEmail(lead),
    getWebsite(lead),
    lead.website_status || "",
    lead.rating || "",
    lead.review_count || lead.rating_count || "",
    lead.lead_score ?? "",
    lead.ai_priority || ""
  ]);

  const csv = [headers, ...rows]
    .map((row) =>
      row
        .map((cell) => `"${String(cell).replaceAll('"', '""')}"`)
        .join(",")
    )
    .join("\n");

  const blob = new Blob([csv], {
    type: "text/csv;charset=utf-8;"
  });

  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = filename;
  link.click();

  URL.revokeObjectURL(url);
}

export function AIPage() {
  const [searchParams] = useSearchParams();

  const [selectedSearchId, setSelectedSearchId] = useState<string>("");
  const [selectedLeadIds, setSelectedLeadIds] = useState<number[]>([]);
  const [aiLead, setAiLead] = useState<Lead | null>(null);

  const [mode, setMode] = useState<"auto" | "custom">("auto");
  const [targetOffer, setTargetOffer] = useState("");
  const [campaignGoal, setCampaignGoal] = useState("");
  const [tone, setTone] = useState(
    "friendly, simple, natural, practical, not too salesy"
  );
  const [targetAudience, setTargetAudience] = useState("local business owner");
  const [outreachChannel, setOutreachChannel] = useState("email");
  const [customInstructions, setCustomInstructions] = useState(
    "Generate complete outreach fields including subject, email body, three follow-ups, Facebook, LinkedIn, and WhatsApp messages."
  );
  const [force, setForce] = useState(true);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const usageQuery = useAiUsage();
  const jobsQuery = useAiJobs();
  const bulkAiMutation = useBulkAiGeneration();
  const { searchesQuery } = useSearches();

  const usage = usageQuery.data;
  const jobs = jobsQuery.data || [];
  const searches = searchesQuery.data || [];

  useEffect(() => {
    const searchIdFromUrl = searchParams.get("search_id");

    if (searchIdFromUrl) {
      setSelectedSearchId(searchIdFromUrl);
    }
  }, [searchParams]);

  const selectedSearch = searches.find(
    (search) => Number(search.id) === Number(selectedSearchId)
  );

  const searchLeadsQuery = useQuery({
    queryKey: ["ai", "search-leads", selectedSearchId],
    queryFn: () => searchService.getSearchLeads(selectedSearchId),
    enabled: Boolean(selectedSearchId),
    refetchInterval: 8000
  });

  const leads = searchLeadsQuery.data || [];

  const filteredSelectedLeadIds = selectedLeadIds.filter((id) =>
    leads.some((lead) => Number(lead.id) === Number(id))
  );

  const allSelected =
    leads.length > 0 &&
    leads.every((lead) => filteredSelectedLeadIds.includes(Number(lead.id)));

  const runningJobs = useMemo(
    () =>
      jobs.filter((job) => {
        const status = getDisplayStatus(job);
        return status === "pending" || status === "running";
      }),
    [jobs]
  );

  function toggleLead(leadId: number) {
    setSelectedLeadIds((current) =>
      current.includes(leadId)
        ? current.filter((id) => id !== leadId)
        : [...current, leadId]
    );
  }

  function toggleAllLeads() {
    if (allSelected) {
      setSelectedLeadIds([]);
    } else {
      setSelectedLeadIds(getLeadIds(leads));
    }
  }

  async function generateAiForLead(lead: Lead) {
    const leadId = Number(lead.id);

    if (!leadId) return;

    await startAiJob([leadId]);
    setAiLead(lead);
  }

  async function generateAiForSelected() {
    if (!filteredSelectedLeadIds.length) {
      alert("Please select at least one business.");
      return;
    }

    await startAiJob(filteredSelectedLeadIds);
  }

  async function generateAiForAllSearchLeads() {
    const ids = getLeadIds(leads);

    if (!ids.length) {
      alert("No leads found in this search.");
      return;
    }

    await startAiJob(ids);
  }

  async function startAiJob(leadIds: number[]) {
    const payload: any = {
      job_type: "full_personalization",
      lead_ids: leadIds,
      force,
      tone,
      outreach_channel: outreachChannel,
      target_audience: targetAudience,
      custom_instructions: customInstructions
    };

    if (mode === "custom") {
      payload.target_offer = targetOffer;
      payload.campaign_goal = campaignGoal;
    }

    await bulkAiMutation.mutateAsync(payload);
    jobsQuery.refetch();
  }

  function handleDownload() {
    if (!leads.length) return;

    const filename = selectedSearch
      ? `moonnova-ai-${getSearchTitle(selectedSearch)
          .replaceAll(" ", "-")
          .replaceAll(",", "")
          .toLowerCase()}.csv`
      : "moonnova-ai-leads.csv";

    downloadCsv(filename, leads);
  }

  const submitLoading = bulkAiMutation.isPending;

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-3 md:flex-row md:items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-950">AI Workspace</h2>
          <p className="mt-1 text-sm text-slate-500">
            Select a search, review businesses, generate AI insights, and view
            outreach messages from one place.
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => jobsQuery.refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh Jobs
          </Button>

          <Button variant="outline" onClick={handleDownload} disabled={!leads.length}>
            <Download className="mr-2 h-4 w-4" />
            Download Leads
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card>
          <CardContent className="flex items-center justify-between p-5">
            <div>
              <p className="text-sm text-slate-500">Credits Remaining</p>
              <p className="mt-2 text-3xl font-bold">
                {usage?.credits_remaining ?? usage?.remaining_this_month ?? 0}
              </p>
            </div>

            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-indigo-50">
              <WalletCards className="h-5 w-5 text-primary" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="flex items-center justify-between p-5">
            <div>
              <p className="text-sm text-slate-500">Credits Used</p>
              <p className="mt-2 text-3xl font-bold">
                {usage?.credits_used ?? usage?.used_this_month ?? 0}
              </p>
            </div>

            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-100">
              <Sparkles className="h-5 w-5 text-slate-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="flex items-center justify-between p-5">
            <div>
              <p className="text-sm text-slate-500">Businesses Loaded</p>
              <p className="mt-2 text-3xl font-bold">{leads.length}</p>
            </div>

            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-green-50">
              <Brain className="h-5 w-5 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="flex items-center justify-between p-5">
            <div>
              <p className="text-sm text-slate-500">Running Jobs</p>
              <p className="mt-2 text-3xl font-bold">{runningJobs.length}</p>
            </div>

            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-amber-50">
              <Clock className="h-5 w-5 text-amber-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="h-5 w-5 text-primary" />
              Select Search
            </CardTitle>
            <CardDescription>
              Choose one search and manage AI for all businesses inside it.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-5">
            <div>
              <Label>Search</Label>
              <select
                className="h-10 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                value={selectedSearchId}
                onChange={(event) => {
                  setSelectedSearchId(event.target.value);
                  setSelectedLeadIds([]);
                }}
              >
                <option value="">Select a search...</option>
                {searches.map((search) => (
                  <option key={search.id} value={search.id}>
                    #{search.id} — {getSearchTitle(search)}
                  </option>
                ))}
              </select>
            </div>

            {selectedSearch && (
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-sm font-semibold text-slate-900">
                  {getSearchTitle(selectedSearch)}
                </p>
                <p className="mt-1 text-xs text-slate-500">
                  Status: {selectedSearch.status} · Mode:{" "}
                  {selectedSearch.scrape_mode || "balanced"}
                </p>
              </div>
            )}

            <div>
              <Label>AI Mode</Label>
              <select
                className="h-10 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                value={mode}
                onChange={(event) =>
                  setMode(event.target.value as "auto" | "custom")
                }
              >
                <option value="auto">Auto Mode — AI decides best offer</option>
                <option value="custom">Custom Mode — I provide offer</option>
              </select>
            </div>

            {mode === "custom" && (
              <div className="space-y-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div>
                  <Label>Target Offer</Label>
                  <textarea
                    className="min-h-20 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                    placeholder="Website design and local SEO improvement"
                    value={targetOffer}
                    onChange={(event) => setTargetOffer(event.target.value)}
                  />
                </div>

                <div>
                  <Label>Campaign Goal</Label>
                  <textarea
                    className="min-h-20 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                    placeholder="Pitch local businesses that need better websites, SEO, or more calls from Google."
                    value={campaignGoal}
                    onChange={(event) => setCampaignGoal(event.target.value)}
                  />
                </div>
              </div>
            )}

            <div>
              <Label>Tone</Label>
              <Input value={tone} onChange={(event) => setTone(event.target.value)} />
            </div>

            <div>
              <Label>Target Audience</Label>
              <Input
                value={targetAudience}
                onChange={(event) => setTargetAudience(event.target.value)}
              />
            </div>

            <div>
              <Label>Outreach Channel</Label>
              <select
                className="h-10 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                value={outreachChannel}
                onChange={(event) => setOutreachChannel(event.target.value)}
              >
                <option value="email">Email</option>
                <option value="facebook">Facebook</option>
                <option value="linkedin">LinkedIn</option>
                <option value="whatsapp">WhatsApp</option>
                <option value="multi_channel">Multi-channel</option>
              </select>
            </div>

            {showAdvanced && (
              <div>
                <Label>Custom Instructions</Label>
                <textarea
                  className="min-h-24 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                  value={customInstructions}
                  onChange={(event) => setCustomInstructions(event.target.value)}
                />
              </div>
            )}

            <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <div>
                <p className="text-sm font-medium text-slate-800">
                  Force regenerate
                </p>
                <p className="text-xs text-slate-500">
                  Replace existing AI insights.
                </p>
              </div>

              <input
                type="checkbox"
                className="h-4 w-4 rounded border-slate-300 text-primary"
                checked={force}
                onChange={(event) => setForce(event.target.checked)}
              />
            </div>

            <button
              type="button"
              className="text-sm font-medium text-primary hover:underline"
              onClick={() => setShowAdvanced(!showAdvanced)}
            >
              {showAdvanced ? "Hide advanced options" : "Show advanced options"}
            </button>

            <div className="grid gap-2">
              <Button
                onClick={generateAiForSelected}
                disabled={submitLoading || !filteredSelectedLeadIds.length}
              >
                {submitLoading ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Sparkles className="mr-2 h-4 w-4" />
                )}
                Generate AI for Selected
              </Button>

              <Button
                variant="outline"
                onClick={generateAiForAllSearchLeads}
                disabled={submitLoading || !leads.length}
              >
                Generate AI for All Businesses
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="xl:col-span-2">
          <CardHeader className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <CardTitle>Businesses in Selected Search</CardTitle>
              <CardDescription>
                Select businesses, generate AI, and open insights without leaving this page.
              </CardDescription>
            </div>

            <div className="text-sm text-slate-500">
              {filteredSelectedLeadIds.length} selected
            </div>
          </CardHeader>

          <CardContent>
            {!selectedSearchId ? (
              <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-10 text-center">
                <Search className="mx-auto h-8 w-8 text-slate-400" />
                <h3 className="mt-3 font-semibold text-slate-800">
                  Select a search first
                </h3>
                <p className="mt-1 text-sm text-slate-500">
                  Businesses from that search will appear here.
                </p>
              </div>
            ) : searchLeadsQuery.isLoading ? (
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
                <Brain className="mx-auto h-8 w-8 text-slate-400" />
                <h3 className="mt-3 font-semibold text-slate-800">
                  No businesses found
                </h3>
                <p className="mt-1 text-sm text-slate-500">
                  This search has no leads yet.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto rounded-2xl border border-slate-200">
                <table className="min-w-[1100px] w-full text-left text-sm">
                  <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                    <tr>
                      <th className="px-4 py-3">
                        <input
                          type="checkbox"
                          checked={allSelected}
                          onChange={toggleAllLeads}
                        />
                      </th>
                      <th className="px-4 py-3">Business</th>
                      <th className="px-4 py-3">Category</th>
                      <th className="px-4 py-3">Phone</th>
                      <th className="px-4 py-3">Website</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">AI</th>
                      <th className="px-4 py-3 text-right">Actions</th>
                    </tr>
                  </thead>

                  <tbody className="divide-y divide-slate-200 bg-white">
                    {leads.map((lead) => {
                      const leadId = Number(lead.id);
                      const selected = filteredSelectedLeadIds.includes(leadId);

                      return (
                        <tr key={lead.id} className="hover:bg-slate-50">
                          <td className="px-4 py-4 align-top">
                            <input
                              type="checkbox"
                              checked={selected}
                              onChange={() => toggleLead(leadId)}
                            />
                          </td>

                          <td className="px-4 py-4 align-top">
                            <button
                              className="text-left"
                              onClick={() => setAiLead(lead)}
                            >
                              <div className="font-semibold text-slate-900 hover:text-primary">
                                {getLeadName(lead)}
                              </div>
                              <div className="mt-1 max-w-[260px] truncate text-xs text-slate-500">
                                {lead.address || lead.location || "-"}
                              </div>
                            </button>
                          </td>

                          <td className="px-4 py-4 align-top text-slate-600">
                            {lead.category || "-"}
                          </td>

                          <td className="px-4 py-4 align-top text-slate-600">
                            {lead.phone || "-"}
                          </td>

                          <td className="px-4 py-4 align-top">
                            {getWebsite(lead) ? (
                              <a
                                href={getWebsite(lead)}
                                target="_blank"
                                rel="noreferrer"
                                className="max-w-[180px] truncate text-primary hover:underline"
                              >
                                {lead.domain || getWebsite(lead)}
                              </a>
                            ) : (
                              <Badge variant="warning">No Website</Badge>
                            )}
                          </td>

                          <td className="px-4 py-4 align-top">
                            <Badge variant="neutral">
                              {lead.website_status || "unknown"}
                            </Badge>
                          </td>

                          <td className="px-4 py-4 align-top">
                            {lead.ai_priority ? (
                              <Badge>{lead.ai_priority}</Badge>
                            ) : (
                              <Badge variant="neutral">Not generated</Badge>
                            )}
                          </td>

                          <td className="px-4 py-4 align-top text-right">
                            <div className="flex justify-end gap-2">
                              <Button
                                variant="outline"
                                className="h-9 px-3"
                                onClick={() => setAiLead(lead)}
                              >
                                <Eye className="mr-2 h-4 w-4" />
                                View AI
                              </Button>

                              <Button
                                className="h-9 px-3"
                                onClick={() => generateAiForLead(lead)}
                                disabled={submitLoading}
                              >
                                <Sparkles className="mr-2 h-4 w-4" />
                                Generate
                              </Button>
                            </div>
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

      <Card>
        <CardHeader>
          <CardTitle>AI Jobs</CardTitle>
          <CardDescription>
            Track AI generation progress and completed jobs.
          </CardDescription>
        </CardHeader>

        <CardContent>
          {jobsQuery.isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((item) => (
                <div
                  key={item}
                  className="h-20 animate-pulse rounded-2xl bg-slate-100"
                />
              ))}
            </div>
          ) : jobs.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-10 text-center">
              <Brain className="mx-auto h-8 w-8 text-slate-400" />
              <h3 className="mt-3 font-semibold text-slate-800">
                No AI jobs yet
              </h3>
              <p className="mt-1 text-sm text-slate-500">
                Generate AI for one business, selected businesses, or the full search.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {jobs.map((job) => {
                const displayStatus = getDisplayStatus(job);
                const progress = getProgress(job);
                const StatusIcon = getStatusIcon(displayStatus);

                return (
                  <div
                    key={job.id}
                    className="rounded-2xl border border-slate-200 bg-white p-4"
                  >
                    <div className="flex flex-col justify-between gap-3 md:flex-row md:items-start">
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="font-semibold text-slate-900">
                            AI Job #{job.id}
                          </p>

                          <Badge variant={getStatusVariant(displayStatus)}>
                            <StatusIcon
                              className={`mr-1 h-3 w-3 ${
                                displayStatus === "running" ? "animate-spin" : ""
                              }`}
                            />
                            {displayStatus}
                          </Badge>

                          <Badge variant="neutral">{job.job_type}</Badge>
                        </div>

                        <p className="mt-1 text-sm text-slate-500">
                          Created {formatDate(job.created_at)}
                        </p>
                      </div>

                      <div className="text-sm text-slate-600">
                        {job.completed_items || 0}/{job.total_items || 0} done
                      </div>
                    </div>

                    <div className="mt-4 h-3 overflow-hidden rounded-full bg-slate-100">
                      <div
                        className="h-full rounded-full bg-primary transition-all"
                        style={{ width: `${progress}%` }}
                      />
                    </div>

                    {job.error_message && (
                      <div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                        {job.error_message}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      <AiInsightDrawer
        lead={aiLead}
        open={Boolean(aiLead)}
        onClose={() => setAiLead(null)}
      />
    </div>
  );
}