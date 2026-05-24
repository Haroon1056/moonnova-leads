import { useMemo, useState } from "react";
import {
  Download,
  ExternalLink,
  Filter,
  Globe2,
  Heart,
  Loader2,
  Mail,
  MapPin,
  Phone,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  Star,
  Trash2,
  X
} from "lucide-react";
import { toast } from "sonner";

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
import { LeadDetailDrawer } from "@/components/leads/LeadDetailDrawer";
import { useExports } from "@/hooks/useExports";
import { useLeads } from "@/hooks/useLeads";
import { useLeadFiltersStore } from "@/store/leadFiltersStore";
import type { CreateExportPayload } from "@/types/export";
import type { Lead } from "@/types/lead";

function leadName(lead: Lead) {
  return lead.name || lead.business_name || "Unnamed business";
}

function leadEmail(lead: Lead) {
  return lead.email_1 || lead.email || lead.email_2 || lead.email_3 || "";
}

function website(lead: Lead) {
  return lead.website || lead.website_url || "";
}

function locationText(lead: Lead) {
  return (
    [lead.city, lead.state, lead.country].filter(Boolean).join(", ") ||
    lead.location ||
    lead.address ||
    "-"
  );
}

function score(lead: Lead) {
  return lead.opportunity_score ?? lead.lead_score ?? 0;
}

function statusVariant(value?: string | null) {
  const v = String(value || "").toLowerCase();

  if (["live", "ok", "active", "completed", "hot", "working"].includes(v)) {
    return "success";
  }

  if (
    ["broken", "down", "error", "failed", "cold", "404", "ssl_error"].includes(v)
  ) {
    return "danger";
  }

  if (["pending", "warm", "unknown", "missing"].includes(v)) {
    return "warning";
  }

  return "neutral";
}

function toAbsoluteUrl(url: string) {
  return url.startsWith("http") ? url : `https://${url}`;
}

function getWebsiteQuality(lead: Lead) {
  const site = website(lead);
  const status = String(lead.website_status || "").toLowerCase();

  if (!site || lead.has_website === false) {
    return {
      label: "No website",
      variant: "warning" as const,
      help: "No website URL was found for this business."
    };
  }

  if (
    lead.is_broken_website ||
    ["broken", "down", "error", "failed", "404", "ssl_error"].includes(status)
  ) {
    return {
      label: lead.website_status || "Website issue",
      variant: "danger" as const,
      help: "Website may be down, expired, broken, SSL issue, or returning an error."
    };
  }

  if (lead.is_social_only) {
    return {
      label: "Social only",
      variant: "warning" as const,
      help: "Business appears to rely on a social page instead of a proper website."
    };
  }

  if (lead.is_free_builder) {
    return {
      label: "Free builder",
      variant: "warning" as const,
      help: "Website may be built on a weak/free builder like Wix, Weebly, or similar."
    };
  }

  return {
    label: lead.website_status || "Working website",
    variant: statusVariant(lead.website_status || "working") as
      | "success"
      | "danger"
      | "warning"
      | "neutral",
    help: "Website exists and no known issue is detected."
  };
}

function readNumber(source: any, keys: string[], fallback = 0) {
  for (const key of keys) {
    const value = source?.[key];

    if (typeof value === "number") return value;

    if (typeof value === "string" && value.trim() !== "" && !Number.isNaN(Number(value))) {
      return Number(value);
    }
  }

  return fallback;
}

export function LeadsPage() {
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  const {
    filters,
    selectedLeadIds,
    leadsQuery,
    bulkEnrichMutation,
    markFavoriteMutation,
    unmarkFavoriteMutation,
    deleteLeadsMutation
  } = useLeads();

  const { createExportMutation } = useExports();

  const { setFilter, resetFilters, toggleSelectedLead, setSelectedLeadIds } =
    useLeadFiltersStore();

  const response = leadsQuery.data;
  const responseAny = response as any;

  const leads = response?.results || [];
  const total = response?.count || leads.length;

  const allSelected =
    leads.length > 0 &&
    leads.every((lead) => selectedLeadIds.includes(Number(lead.id)));

  const statsSource =
    responseAny?.stats ||
    responseAny?.summary ||
    responseAny?.aggregates ||
    responseAny?.meta ||
    {};

  const stats = useMemo(() => {
    const pageEmails = leads.filter((lead) => leadEmail(lead)).length;
    const pageWithWebsite = leads.filter((lead) => website(lead)).length;
    const pageOpportunities = leads.filter(
      (lead) =>
        !website(lead) ||
        lead.has_website === false ||
        lead.is_broken_website ||
        lead.is_social_only ||
        lead.is_free_builder
    ).length;

    return {
      total,
      emails: readNumber(
        statsSource,
        [
          "emails_found",
          "total_emails",
          "with_email",
          "leads_with_email",
          "email_count"
        ],
        pageEmails
      ),
      withWebsite: readNumber(
        statsSource,
        [
          "with_website",
          "total_with_website",
          "websites",
          "leads_with_website",
          "website_count"
        ],
        pageWithWebsite
      ),
      opportunities: readNumber(
        statsSource,
        [
          "web_opportunities",
          "website_opportunities",
          "website_issues",
          "total_opportunities",
          "no_website_or_issue"
        ],
        pageOpportunities
      )
    };
  }, [leads, statsSource, total]);

  function selectPage() {
    if (allSelected) {
      setSelectedLeadIds([]);
      return;
    }

    setSelectedLeadIds(leads.map((lead) => Number(lead.id)));
  }

  async function handleExport() {
    if (leads.length === 0) {
      toast.error("No leads available to export.");
      return;
    }

    try {
      const payload = {
        export_type: "csv",
        file_format: "csv",
        export_scope: selectedLeadIds.length > 0 ? "selected_leads" : "filtered",
        lead_ids: selectedLeadIds.length > 0 ? selectedLeadIds : undefined,
        filters: selectedLeadIds.length > 0 ? undefined : { ...filters },
        include_basic_fields: true,
        include_contact_fields: true,
        include_website_fields: true,
        include_enrichment_fields: true,
        include_ai_fields: true
      } as CreateExportPayload;

      await createExportMutation.mutateAsync(payload);

      toast.success(
        selectedLeadIds.length > 0
          ? "Export started for selected leads. Open Exports page to download when ready."
          : "Filtered export started. Open Exports page to download when ready."
      );
    } catch {
      toast.error("Export failed. Please try again.");
    }
  }

  return (
    <div className="space-y-6 overflow-x-hidden">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div className="min-w-0">
          <p className="text-xs font-black uppercase tracking-[0.22em] text-primaryDark">
            Lead Database
          </p>
          <h2 className="mt-2 text-3xl font-black tracking-tight text-slate-950">
            Review, filter, and qualify leads
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
            Manage scraped businesses, website quality, email enrichment, and outreach
            readiness.
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => setShowFilters((value) => !value)}>
            <Filter className="mr-2 h-4 w-4" />
            Filters
          </Button>

          <Button variant="outline" onClick={() => leadsQuery.refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[
          [
            "Total Leads",
            stats.total,
            Search,
            "All leads matching current filters"
          ],
          [
            "Emails Found",
            stats.emails,
            Mail,
            "Total leads with at least one email"
          ],
          [
            "With Website",
            stats.withWebsite,
            Globe2,
            "Total businesses with a website URL"
          ],
          [
            "Web Opportunities",
            stats.opportunities,
            Sparkles,
            "Total no website, broken site, social-only, or weak builder"
          ]
        ].map(([label, value, Icon, description]: any) => (
          <Card key={label}>
            <CardContent className="flex items-center justify-between gap-4 p-5">
              <div className="min-w-0">
                <p className="text-sm font-bold text-slate-500">{label}</p>
                <p className="mt-2 text-3xl font-black text-slate-950">
                  {Number(value).toLocaleString()}
                </p>
                <p className="mt-1 text-xs leading-5 text-slate-500">
                  {description}
                </p>
              </div>

              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-primarySoft text-primaryDark ring-1 ring-orange-200">
                <Icon className="h-5 w-5" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="min-w-0">
        <CardHeader className="gap-4">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <CardTitle>Leads</CardTitle>
              <CardDescription>
                Showing {leads.length.toLocaleString()} of{" "}
                {total.toLocaleString()} records.
              </CardDescription>
            </div>

            <div className="flex flex-col gap-2 sm:flex-row">
              <div className="relative min-w-0 sm:min-w-72">
                <Search className="pointer-events-none absolute left-3 top-3.5 h-4 w-4 text-slate-400" />
                <Input
                  className="pl-9"
                  placeholder="Search name, phone, email, city..."
                  value={filters.search || ""}
                  onChange={(event) => setFilter("search", event.target.value)}
                />
              </div>

              <Button
                variant="outline"
                onClick={handleExport}
                disabled={createExportMutation.isPending || leads.length === 0}
              >
                {createExportMutation.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Download className="mr-2 h-4 w-4" />
                )}
                Export
              </Button>
            </div>
          </div>

          {showFilters && (
            <div className="grid gap-3 rounded-2xl border border-borderSoft bg-cardSoft p-4 md:grid-cols-3 xl:grid-cols-6">
              <div>
                <Label>Keyword</Label>
                <Input
                  placeholder="e.g. plumber"
                  value={filters.keyword || ""}
                  onChange={(event) => setFilter("keyword", event.target.value)}
                />
              </div>

              <div>
                <Label>Location</Label>
                <Input
                  placeholder="e.g. Perth"
                  value={filters.location || ""}
                  onChange={(event) => setFilter("location", event.target.value)}
                />
              </div>

              <div>
                <Label>Category</Label>
                <Input
                  placeholder="e.g. roofing"
                  value={filters.category || ""}
                  onChange={(event) => setFilter("category", event.target.value)}
                />
              </div>

              <div>
                <Label>Email</Label>
                <select
                  className="h-11 w-full rounded-xl border border-borderSoft bg-white px-3 text-sm"
                  value={String(filters.has_email ?? "")}
                  onChange={(event) =>
                    setFilter(
                      "has_email",
                      event.target.value === ""
                        ? ""
                        : event.target.value === "true"
                    )
                  }
                >
                  <option value="">Any</option>
                  <option value="true">Has email</option>
                  <option value="false">No email</option>
                </select>
              </div>

              <div>
                <Label>Website</Label>
                <select
                  className="h-11 w-full rounded-xl border border-borderSoft bg-white px-3 text-sm"
                  value={String(filters.has_website ?? "")}
                  onChange={(event) =>
                    setFilter(
                      "has_website",
                      event.target.value === ""
                        ? ""
                        : event.target.value === "true"
                    )
                  }
                >
                  <option value="">Any</option>
                  <option value="true">Has website</option>
                  <option value="false">No website</option>
                </select>
              </div>

              <div className="flex items-end">
                <Button variant="outline" className="w-full" onClick={resetFilters}>
                  <X className="mr-2 h-4 w-4" />
                  Reset
                </Button>
              </div>
            </div>
          )}
        </CardHeader>

        <CardContent>
          {selectedLeadIds.length > 0 && (
            <div className="mb-4 flex flex-col gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-3 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm font-bold text-amber-900">
                {selectedLeadIds.length} leads selected
              </p>

              <div className="flex flex-wrap gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => bulkEnrichMutation.mutate(selectedLeadIds)}
                  disabled={bulkEnrichMutation.isPending}
                >
                  Enrich
                </Button>

                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => markFavoriteMutation.mutate(selectedLeadIds)}
                  disabled={markFavoriteMutation.isPending}
                >
                  Favorite
                </Button>

                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => unmarkFavoriteMutation.mutate(selectedLeadIds)}
                  disabled={unmarkFavoriteMutation.isPending}
                >
                  Unfavorite
                </Button>

                <Button
                  size="sm"
                  variant="danger"
                  onClick={() => deleteLeadsMutation.mutate(selectedLeadIds)}
                  disabled={deleteLeadsMutation.isPending}
                >
                  Delete
                </Button>
              </div>
            </div>
          )}

          {leadsQuery.isLoading ? (
            <TableSkeleton />
          ) : leads.length === 0 ? (
            <div className="flex min-h-72 flex-col items-center justify-center rounded-2xl border border-dashed border-borderSoft bg-white/70 p-8 text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primarySoft text-primaryDark">
                <Search className="h-7 w-7" />
              </div>
              <h3 className="mt-4 text-lg font-black text-slate-950">
                No leads found
              </h3>
              <p className="mt-2 max-w-md text-sm leading-6 text-slate-500">
                Start a search or clear filters to view lead records.
              </p>
            </div>
          ) : (
            <>
              <div className="table-shell hidden lg:block">
                <div className="table-scroll contained-scroll">
                  <table className="data-table leads-table">
                    <thead>
                      <tr>
                        <th className="w-10">
                          <input
                            type="checkbox"
                            checked={allSelected}
                            onChange={selectPage}
                          />
                        </th>
                        <th>Business</th>
                        <th>Contact</th>
                        <th>Website Quality</th>
                        <th>Location</th>
                        <th>Score</th>
                        <th className="text-right">Actions</th>
                      </tr>
                    </thead>

                    <tbody>
                      {leads.map((lead) => {
                        const email = leadEmail(lead);
                        const site = website(lead);
                        const quality = getWebsiteQuality(lead);

                        return (
                          <tr key={lead.id}>
                            <td>
                              <input
                                type="checkbox"
                                checked={selectedLeadIds.includes(Number(lead.id))}
                                onChange={() => toggleSelectedLead(Number(lead.id))}
                              />
                            </td>

                            <td>
                              <button
                                className="max-w-[260px] text-left"
                                onClick={() => setSelectedLead(lead)}
                              >
                                <div className="font-black text-slate-950">
                                  {leadName(lead)}
                                </div>
                                <div className="mt-1 text-xs font-medium text-slate-500">
                                  {lead.category ||
                                    lead.keyword ||
                                    "Uncategorized"}
                                </div>
                              </button>
                            </td>

                            <td>
                              <div className="space-y-1 text-xs font-medium text-slate-600">
                                {lead.phone && (
                                  <div className="flex items-center gap-1">
                                    <Phone className="h-3.5 w-3.5" />
                                    {lead.phone}
                                  </div>
                                )}

                                {email && (
                                  <div className="flex items-center gap-1">
                                    <Mail className="h-3.5 w-3.5" />
                                    {email}
                                  </div>
                                )}

                                {!lead.phone && !email && (
                                  <span className="text-slate-400">
                                    No contact yet
                                  </span>
                                )}
                              </div>
                            </td>

                            <td>
                              <div className="space-y-2">
                                {site ? (
                                  <a
                                    href={toAbsoluteUrl(site)}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="inline-flex max-w-[260px] items-center gap-1 truncate text-xs font-bold text-primaryDark hover:underline"
                                  >
                                    <Globe2 className="h-3.5 w-3.5 shrink-0" />
                                    <span className="truncate">{site}</span>
                                    <ExternalLink className="h-3 w-3 shrink-0" />
                                  </a>
                                ) : (
                                  <span className="text-xs font-medium text-slate-400">
                                    No website URL
                                  </span>
                                )}

                                <div>
                                  <Badge variant={quality.variant}>
                                    <ShieldCheck className="mr-1 h-3.5 w-3.5" />
                                    {quality.label}
                                  </Badge>
                                  <p className="mt-1 max-w-[280px] text-[11px] leading-4 text-slate-500">
                                    {quality.help}
                                  </p>
                                </div>
                              </div>
                            </td>

                            <td className="text-xs font-medium text-slate-600">
                              <MapPin className="mr-1 inline h-3.5 w-3.5" />
                              {locationText(lead)}
                            </td>

                            <td>
                              <div className="flex items-center gap-1 font-black">
                                <Star className="h-4 w-4 text-amber-600" />
                                {score(lead)}
                              </div>
                            </td>

                            <td>
                              <div className="flex justify-end gap-1">
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() =>
                                    markFavoriteMutation.mutate([Number(lead.id)])
                                  }
                                >
                                  <Heart className="h-4 w-4" />
                                </Button>

                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() =>
                                    deleteLeadsMutation.mutate([Number(lead.id)])
                                  }
                                >
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="grid gap-3 lg:hidden">
                {leads.map((lead) => {
                  const email = leadEmail(lead);
                  const site = website(lead);
                  const quality = getWebsiteQuality(lead);

                  return (
                    <div
                      key={lead.id}
                      className="rounded-2xl border border-borderSoft bg-white p-4 shadow-sm"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <button
                            className="text-left"
                            onClick={() => setSelectedLead(lead)}
                          >
                            <div className="truncate font-black text-slate-950">
                              {leadName(lead)}
                            </div>
                            <div className="mt-1 text-xs font-medium text-slate-500">
                              {lead.category || lead.keyword || "Uncategorized"}
                            </div>
                          </button>
                        </div>

                        <input
                          type="checkbox"
                          checked={selectedLeadIds.includes(Number(lead.id))}
                          onChange={() => toggleSelectedLead(Number(lead.id))}
                        />
                      </div>

                      <div className="mt-3 grid gap-2 text-xs text-slate-600">
                        {lead.phone && (
                          <div className="flex items-center gap-1">
                            <Phone className="h-3.5 w-3.5" />
                            {lead.phone}
                          </div>
                        )}

                        {email && (
                          <div className="flex items-center gap-1">
                            <Mail className="h-3.5 w-3.5" />
                            {email}
                          </div>
                        )}

                        <div className="flex items-center gap-1">
                          <MapPin className="h-3.5 w-3.5" />
                          {locationText(lead)}
                        </div>
                      </div>

                      <div className="mt-3 space-y-2">
                        {site && (
                          <a
                            href={toAbsoluteUrl(site)}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex max-w-full items-center gap-1 truncate text-xs font-bold text-primaryDark"
                          >
                            <Globe2 className="h-3.5 w-3.5 shrink-0" />
                            <span className="truncate">{site}</span>
                            <ExternalLink className="h-3 w-3 shrink-0" />
                          </a>
                        )}

                        <div className="flex flex-wrap items-center gap-2">
                          <Badge variant={quality.variant}>
                            {quality.label}
                          </Badge>

                          <span className="inline-flex items-center gap-1 text-xs font-bold text-slate-700">
                            <Star className="h-3.5 w-3.5 text-amber-600" />
                            {score(lead)}
                          </span>
                        </div>

                        <p className="text-[11px] leading-4 text-slate-500">
                          {quality.help}
                        </p>
                      </div>

                      <div className="mt-3 flex justify-end gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setSelectedLead(lead)}
                        >
                          View
                        </Button>

                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() =>
                            markFavoriteMutation.mutate([Number(lead.id)])
                          }
                        >
                          Favorite
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          )}

          <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-xs font-medium text-slate-500">
              Page {filters.page || 1} • {filters.page_size || 50} rows per page
            </p>

            <div className="flex gap-2">
              <Button
                variant="outline"
                disabled={(filters.page || 1) <= 1}
                onClick={() =>
                  setFilter("page", Math.max(1, Number(filters.page || 1) - 1))
                }
              >
                Previous
              </Button>

              <Button
                variant="outline"
                disabled={!response?.next}
                onClick={() => setFilter("page", Number(filters.page || 1) + 1)}
              >
                Next
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <LeadDetailDrawer
        lead={selectedLead}
        open={Boolean(selectedLead)}
        onClose={() => setSelectedLead(null)}
        onEnrich={(leadId) => bulkEnrichMutation.mutate([leadId])}
        onFavorite={(leadId) => markFavoriteMutation.mutate([leadId])}
      />
    </div>
  );
}