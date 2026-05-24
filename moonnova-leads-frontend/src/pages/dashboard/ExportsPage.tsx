import {
  CheckCircle2,
  Clock,
  Download,
  FileSpreadsheet,
  Loader2,
  RefreshCw,
  Search,
  Trash2,
  XCircle
} from "lucide-react";
import { useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { useExports } from "@/hooks/useExports";
import { useSearches } from "@/hooks/useSearches";
import { useLeadLists } from "@/hooks/useLeads";
import { formatDate } from "@/lib/utils";
import type { ExportHistory } from "@/types/export";
import type { SearchJob } from "@/types/search";
import type { SavedLeadList } from "@/types/lead-list";

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

function getDisplayStatus(exportItem: ExportHistory) {
  if (
    exportItem.status === "running" &&
    exportItem.file_url &&
    exportItem.total_rows
  ) {
    return "completed";
  }

  return exportItem.status;
}

function getSearchTitle(search: SearchJob) {
  const keywords = search.keywords?.join(", ") || search.keyword || "Search";
  const locations =
    search.locations?.join(", ") || search.location || "Location";

  return `${keywords} in ${locations}`;
}

function getLeadListTitle(list: SavedLeadList) {
  const count = list.leads_count ?? list.leads?.length ?? 0;
  return `${list.name} (${count} leads)`;
}

function formatScope(scope?: string) {
  if (!scope) return "Unknown";
  return scope.replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

export function ExportsPage() {
  const [exportScope, setExportScope] = useState<"all_leads" | "search" | "lead_list">(
    "search"
  );
  const [fileFormat, setFileFormat] = useState<"csv" | "xlsx">("csv");
  const [selectedSearchId, setSelectedSearchId] = useState("");
  const [selectedListId, setSelectedListId] = useState("");

  const [includeBasic, setIncludeBasic] = useState(true);
  const [includeContact, setIncludeContact] = useState(true);
  const [includeWebsite, setIncludeWebsite] = useState(true);
  const [includeEnrichment, setIncludeEnrichment] = useState(true);
  const [includeAi, setIncludeAi] = useState(true);
  const [includeRaw, setIncludeRaw] = useState(false);

  const {
    exportsQuery,
    createExportMutation,
    downloadExportMutation,
    deleteExportMutation
  } = useExports();

  const { searchesQuery } = useSearches();
  const { leadListsQuery } = useLeadLists();

  const exports = exportsQuery.data || [];
  const searches = searchesQuery.data || [];
  const leadLists = leadListsQuery.data || [];

  const runningExports = useMemo(
    () =>
      exports.filter((item) => {
        const status = getDisplayStatus(item);
        return status === "pending" || status === "running";
      }),
    [exports]
  );

  async function handleCreateExport() {
    const payload: any = {
      export_scope: exportScope,
      export_type: fileFormat,
      file_format: fileFormat,
      include_basic_fields: includeBasic,
      include_contact_fields: includeContact,
      include_website_fields: includeWebsite,
      include_enrichment_fields: includeEnrichment,
      include_ai_fields: includeAi,
      include_raw_data: includeRaw
    };

    if (exportScope === "search") {
      if (!selectedSearchId) {
        alert("Please select a search.");
        return;
      }

      payload.search = Number(selectedSearchId);
      payload.search_id = Number(selectedSearchId);
    }

    if (exportScope === "lead_list") {
      if (!selectedListId) {
        alert("Please select a lead list.");
        return;
      }

      payload.lead_list = Number(selectedListId);
      payload.lead_list_id = Number(selectedListId);
    }

    await createExportMutation.mutateAsync(payload);
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-3 md:flex-row md:items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-950">Exports</h2>
          <p className="mt-1 text-sm text-slate-500">
            Export scraped leads, enrichment data, and AI outreach fields.
          </p>
        </div>

        <Button variant="outline" onClick={() => exportsQuery.refetch()}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="flex items-center justify-between p-5">
            <div>
              <p className="text-sm text-slate-500">Total Exports</p>
              <p className="mt-2 text-3xl font-bold">{exports.length}</p>
            </div>

            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-indigo-50">
              <FileSpreadsheet className="h-5 w-5 text-primary" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="flex items-center justify-between p-5">
            <div>
              <p className="text-sm text-slate-500">Running</p>
              <p className="mt-2 text-3xl font-bold">{runningExports.length}</p>
            </div>

            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-amber-50">
              <Clock className="h-5 w-5 text-amber-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="flex items-center justify-between p-5">
            <div>
              <p className="text-sm text-slate-500">Completed</p>
              <p className="mt-2 text-3xl font-bold">
                {
                  exports.filter(
                    (item) => getDisplayStatus(item) === "completed"
                  ).length
                }
              </p>
            </div>

            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-green-50">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-1">
          <CardHeader>
            <CardTitle>Create Export</CardTitle>
            <CardDescription>
              Choose source, format, and fields to include.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-5">
            <div>
              <Label>Export Source</Label>
              <select
                className="h-10 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                value={exportScope}
                onChange={(event) =>
                  setExportScope(event.target.value as "all_leads" | "search" | "lead_list")
                }
              >
                <option value="search">One Search</option>
                <option value="lead_list">Lead List</option>
                <option value="all_leads">All Leads</option>
              </select>
            </div>

            {exportScope === "search" && (
              <div>
                <Label>Select Search</Label>
                <select
                  className="h-10 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                  value={selectedSearchId}
                  onChange={(event) => setSelectedSearchId(event.target.value)}
                >
                  <option value="">Select a search...</option>
                  {searches.map((search) => (
                    <option key={search.id} value={search.id}>
                      #{search.id} — {getSearchTitle(search)}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {exportScope === "lead_list" && (
              <div>
                <Label>Select Lead List</Label>
                <select
                  className="h-10 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                  value={selectedListId}
                  onChange={(event) => setSelectedListId(event.target.value)}
                >
                  <option value="">Select a lead list...</option>
                  {leadLists.map((list) => (
                    <option key={list.id} value={list.id}>
                      #{list.id} — {getLeadListTitle(list)}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div>
              <Label>File Format</Label>
              <select
                className="h-10 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                value={fileFormat}
                onChange={(event) =>
                  setFileFormat(event.target.value as "csv" | "xlsx")
                }
              >
                <option value="csv">CSV</option>
                <option value="xlsx">Excel XLSX</option>
              </select>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="mb-3 text-sm font-semibold text-slate-900">
                Fields to Include
              </p>

              <div className="space-y-3 text-sm">
                <label className="flex items-center justify-between gap-3">
                  <span>Basic business fields</span>
                  <input
                    type="checkbox"
                    checked={includeBasic}
                    onChange={(event) => setIncludeBasic(event.target.checked)}
                  />
                </label>

                <label className="flex items-center justify-between gap-3">
                  <span>Contact fields</span>
                  <input
                    type="checkbox"
                    checked={includeContact}
                    onChange={(event) => setIncludeContact(event.target.checked)}
                  />
                </label>

                <label className="flex items-center justify-between gap-3">
                  <span>Website fields</span>
                  <input
                    type="checkbox"
                    checked={includeWebsite}
                    onChange={(event) => setIncludeWebsite(event.target.checked)}
                  />
                </label>

                <label className="flex items-center justify-between gap-3">
                  <span>Enrichment fields</span>
                  <input
                    type="checkbox"
                    checked={includeEnrichment}
                    onChange={(event) =>
                      setIncludeEnrichment(event.target.checked)
                    }
                  />
                </label>

                <label className="flex items-center justify-between gap-3">
                  <span>AI insight fields</span>
                  <input
                    type="checkbox"
                    checked={includeAi}
                    onChange={(event) => setIncludeAi(event.target.checked)}
                  />
                </label>

                <label className="flex items-center justify-between gap-3">
                  <span>Raw data</span>
                  <input
                    type="checkbox"
                    checked={includeRaw}
                    onChange={(event) => setIncludeRaw(event.target.checked)}
                  />
                </label>
              </div>
            </div>

            <Button
              className="w-full"
              onClick={handleCreateExport}
              disabled={createExportMutation.isPending}
            >
              {createExportMutation.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <FileSpreadsheet className="mr-2 h-4 w-4" />
              )}
              Create Export
            </Button>
          </CardContent>
        </Card>

        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle>Export History</CardTitle>
            <CardDescription>
              Download completed exports or review failed exports.
            </CardDescription>
          </CardHeader>

          <CardContent>
            {exportsQuery.isLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((item) => (
                  <div
                    key={item}
                    className="h-20 animate-pulse rounded-2xl bg-slate-100"
                  />
                ))}
              </div>
            ) : exports.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-10 text-center">
                <Search className="mx-auto h-8 w-8 text-slate-400" />
                <h3 className="mt-3 font-semibold text-slate-800">
                  No exports yet
                </h3>
                <p className="mt-1 text-sm text-slate-500">
                  Create your first export from the form.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {exports.map((exportItem) => {
                  const status = getDisplayStatus(exportItem);
                  const StatusIcon = getStatusIcon(status);
                  // const downloadUrl = getDownloadUrl(exportItem);

                  return (
                    <div
                      key={exportItem.id}
                      className="rounded-2xl border border-slate-200 bg-white p-4"
                    >
                      <div className="flex flex-col justify-between gap-3 md:flex-row md:items-start">
                        <div>
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="font-semibold text-slate-900">
                              Export #{exportItem.id}
                            </p>

                            <Badge variant={getStatusVariant(status)}>
                              <StatusIcon
                                className={`mr-1 h-3 w-3 ${
                                  status === "running" ? "animate-spin" : ""
                                }`}
                              />
                              {status}
                            </Badge>

                            <Badge variant="neutral">
                              {exportItem.file_format ||
                                exportItem.export_type ||
                                "csv"}
                            </Badge>

                            <Badge variant="neutral">
                              {formatScope(exportItem.export_scope)}
                            </Badge>
                          </div>

                          <p className="mt-1 text-sm text-slate-500">
                            Created {formatDate(exportItem.created_at)}
                          </p>

                          {exportItem.file_name && (
                            <p className="mt-1 text-sm text-slate-500">
                              File: {exportItem.file_name}
                            </p>
                          )}
                        </div>

                        <div className="flex flex-wrap gap-2">
                          {status === "completed" && (
                            <Button
                              variant="outline"
                              onClick={() => downloadExportMutation.mutate(exportItem)}
                              disabled={downloadExportMutation.isPending}
                            >
                              {downloadExportMutation.isPending ? (
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              ) : (
                                <Download className="mr-2 h-4 w-4" />
                              )}
                              Download
                            </Button>
                          )}

                          <Button
                            variant="danger"
                            onClick={() => {
                              if (confirm("Delete this export?")) {
                                deleteExportMutation.mutate(exportItem.id);
                              }
                            }}
                          >
                            <Trash2 className="mr-2 h-4 w-4" />
                            Delete
                          </Button>
                        </div>
                      </div>

                      <div className="mt-4 grid gap-3 md:grid-cols-3">
                        <div className="rounded-xl bg-slate-50 p-3">
                          <p className="text-xs text-slate-500">Rows</p>
                          <p className="mt-1 font-semibold text-slate-900">
                            {exportItem.total_rows || 0}
                          </p>
                        </div>

                        <div className="rounded-xl bg-slate-50 p-3">
                          <p className="text-xs text-slate-500">Scope</p>
                          <p className="mt-1 font-semibold text-slate-900">
                            {formatScope(exportItem.export_scope)}
                          </p>
                        </div>

                        <div className="rounded-xl bg-slate-50 p-3">
                          <p className="text-xs text-slate-500">Format</p>
                          <p className="mt-1 font-semibold uppercase text-slate-900">
                            {exportItem.file_format ||
                              exportItem.export_type ||
                              "csv"}
                          </p>
                        </div>
                      </div>

                      {exportItem.error_message && (
                        <div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                          {exportItem.error_message}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}