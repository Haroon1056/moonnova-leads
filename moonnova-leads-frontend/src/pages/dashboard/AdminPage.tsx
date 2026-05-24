import {
  Activity,
  AlertTriangle,
  Bot,
  CheckCircle2,
  Clock,
  Database,
  HardDrive,
  Loader2,
  RefreshCw,
  Search,
  Server,
  ShieldCheck,
  Sparkles,
  UserCheck,
  UserX,
  Users,
  XCircle
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card";

import {
  useAdminAiJobs,
  useAdminAiSummary,
  useAdminOverview,
  useAdminSearches,
  useAdminUserActions,
  useAdminUsers,
  useMonitoringEvents,
  useSystemHealth
} from "@/hooks/useAdmin";

import { formatDate } from "@/lib/utils";
import type { MonitoringEvent } from "@/types/admin";

function getStatusVariant(status?: string) {
  const value = String(status || "").toLowerCase();

  if (
    ["ok", "healthy", "connected", "running", "completed", "active"].includes(
      value
    )
  ) {
    return "success";
  }

  if (["warning", "pending", "degraded", "unknown"].includes(value)) {
    return "warning";
  }

  if (
    [
      "failed",
      "error",
      "down",
      "disconnected",
      "unhealthy",
      "inactive",
      "suspended"
    ].includes(value)
  ) {
    return "danger";
  }

  return "neutral";
}

function getEventVariant(level?: string) {
  const value = String(level || "").toLowerCase();

  if (["error", "critical"].includes(value)) return "danger";
  if (["warning", "warn"].includes(value)) return "warning";
  if (["info", "success"].includes(value)) return "success";

  return "neutral";
}

function getEventIcon(event: MonitoringEvent) {
  const level = String(event.level || "").toLowerCase();

  if (["error", "critical"].includes(level)) return XCircle;
  if (["warning", "warn"].includes(level)) return AlertTriangle;

  return Activity;
}

function StatCard({
  title,
  value,
  icon: Icon,
  subtitle
}: {
  title: string;
  value: string | number;
  icon: any;
  subtitle?: string;
}) {
  return (
    <Card>
      <CardContent className="flex items-center justify-between p-5">
        <div>
          <p className="text-sm text-slate-500">{title}</p>
          <p className="mt-2 text-3xl font-bold text-slate-950">{value}</p>

          {subtitle && (
            <p className="mt-1 text-xs text-slate-500">{subtitle}</p>
          )}
        </div>

        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-indigo-50">
          <Icon className="h-5 w-5 text-primary" />
        </div>
      </CardContent>
    </Card>
  );
}

function HealthRow({
  label,
  value,
  icon: Icon
}: {
  label: string;
  value?: string;
  icon: any;
}) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white p-3">
      <div className="flex items-center gap-2">
        <Icon className="h-4 w-4 text-slate-400" />
        <span className="text-sm font-medium text-slate-700">{label}</span>
      </div>

      <Badge variant={getStatusVariant(value)}>{value || "unknown"}</Badge>
    </div>
  );
}

export function AdminPage() {
  const overviewQuery = useAdminOverview();
  const usersQuery = useAdminUsers();
  const healthQuery = useSystemHealth();
  const eventsQuery = useMonitoringEvents();
  const aiSummaryQuery = useAdminAiSummary();
  const aiJobsQuery = useAdminAiJobs();
  const searchesQuery = useAdminSearches();

  const { activateUserMutation, suspendUserMutation } = useAdminUserActions();

  const overview = overviewQuery.data;
  const users = usersQuery.data || [];
  const health = healthQuery.data;
  const events = eventsQuery.data || [];
  const aiSummary = aiSummaryQuery.data;
  const aiJobs = aiJobsQuery.data || [];
  const searches = searchesQuery.data || [];

  const loading =
    overviewQuery.isLoading ||
    usersQuery.isLoading ||
    healthQuery.isLoading ||
    eventsQuery.isLoading ||
    aiSummaryQuery.isLoading ||
    aiJobsQuery.isLoading ||
    searchesQuery.isLoading;

  function refreshAll() {
    overviewQuery.refetch();
    usersQuery.refetch();
    healthQuery.refetch();
    eventsQuery.refetch();
    aiSummaryQuery.refetch();
    aiJobsQuery.refetch();
    searchesQuery.refetch();
  }

  if (loading) {
    return (
      <div className="flex min-h-[350px] items-center justify-center">
        <Loader2 className="h-7 w-7 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-3 md:flex-row md:items-center">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-6 w-6 text-primary" />
            <h2 className="text-2xl font-bold text-slate-950">
              Admin Dashboard
            </h2>
          </div>

          <p className="mt-1 text-sm text-slate-500">
            Admin-only control center for users, AI usage, monitoring, system
            health, and platform activity.
          </p>
        </div>

        <Button variant="outline" onClick={refreshAll}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Total Users"
          value={overview?.users_total ?? users.length}
          icon={Users}
          subtitle={`${overview?.active_users ?? 0} active · ${
            overview?.staff_users ?? 0
          } staff`}
        />

        <StatCard
          title="Total Searches"
          value={overview?.searches_total ?? 0}
          icon={Search}
          subtitle={`${overview?.running_searches ?? 0} running`}
        />

        <StatCard
          title="Total Leads"
          value={overview?.leads_total ?? 0}
          icon={Database}
        />

        <StatCard
          title="AI Jobs"
          value={overview?.ai_jobs_total ?? aiJobs.length}
          icon={Bot}
          subtitle={`${overview?.ai_jobs_running ?? 0} running · ${
            overview?.ai_jobs_failed ?? 0
          } failed`}
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Server className="h-5 w-5 text-primary" />
              System Health
            </CardTitle>
            <CardDescription>
              Core backend services and worker status.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-3">
            <HealthRow label="Overall" value={health?.status} icon={Activity} />
            <HealthRow
              label="Database"
              value={health?.database}
              icon={Database}
            />
            <HealthRow
              label="Redis / Cache"
              value={health?.redis || health?.cache}
              icon={Server}
            />
            <HealthRow label="Celery" value={health?.celery} icon={RefreshCw} />
            <HealthRow
              label="Scraper Worker"
              value={health?.scraper_worker}
              icon={Search}
            />
            <HealthRow
              label="Enrichment Worker"
              value={health?.enrichment_worker}
              icon={Sparkles}
            />
            <HealthRow
              label="Default Worker"
              value={health?.default_worker}
              icon={Clock}
            />
            <HealthRow label="Storage" value={health?.storage} icon={HardDrive} />
            <HealthRow
              label="AI Provider"
              value={health?.ai_provider}
              icon={Bot}
            />

            {health?.checked_at && (
              <p className="pt-2 text-xs text-slate-500">
                Last checked: {formatDate(health.checked_at)}
              </p>
            )}

            {health?.worker_names && health.worker_names.length > 0 && (
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <p className="text-xs font-semibold uppercase text-slate-500">
                  Workers
                </p>
                <p className="mt-2 text-xs leading-5 text-slate-600">
                  {health.worker_names.join(", ")}
                </p>
              </div>
            )}

            <div className="grid gap-3 pt-2 md:grid-cols-3 xl:grid-cols-1">
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <p className="text-xs text-slate-500">Stuck Searches</p>
                <p className="mt-1 font-semibold text-slate-900">
                  {health?.stuck_searches ?? 0}
                </p>
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <p className="text-xs text-slate-500">Failed Exports 24h</p>
                <p className="mt-1 font-semibold text-slate-900">
                  {health?.failed_exports_24h ?? 0}
                </p>
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <p className="text-xs text-slate-500">Failed AI Jobs 24h</p>
                <p className="mt-1 font-semibold text-slate-900">
                  {health?.failed_ai_jobs_24h ?? 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              AI Admin
            </CardTitle>
            <CardDescription>
              AI usage, running jobs, quota issues, and failed jobs.
            </CardDescription>
          </CardHeader>

          <CardContent>
            <div className="grid gap-4 md:grid-cols-4">
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-xs text-slate-500">Provider</p>
                <p className="mt-1 font-semibold text-slate-900">
                  {aiSummary?.provider || "Gemini"}
                </p>
              </div>

              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-xs text-slate-500">Jobs Running</p>
                <p className="mt-1 font-semibold text-slate-900">
                  {aiSummary?.jobs_running ?? 0}
                </p>
              </div>

              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-xs text-slate-500">Credits Used</p>
                <p className="mt-1 font-semibold text-slate-900">
                  {aiSummary?.credits_used_this_month ??
                    aiSummary?.credits_used_total ??
                    0}
                </p>
              </div>

              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-xs text-slate-500">Quota Errors</p>
                <p className="mt-1 font-semibold text-slate-900">
                  {aiSummary?.quota_errors ?? 0}
                </p>
              </div>
            </div>

            {aiSummary?.last_error && (
              <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                {aiSummary.last_error}
              </div>
            )}

            <div className="mt-5 overflow-x-auto rounded-2xl border border-slate-200">
              <table className="min-w-[900px] w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Job</th>
                    <th className="px-4 py-3">User</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Progress</th>
                    <th className="px-4 py-3">Credits</th>
                    <th className="px-4 py-3">Created</th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-slate-200 bg-white">
                  {aiJobs.slice(0, 10).map((job) => (
                    <tr key={job.id} className="hover:bg-slate-50">
                      <td className="px-4 py-4">
                        <div className="font-semibold text-slate-900">
                          AI Job #{job.id}
                        </div>
                        <div className="text-xs text-slate-500">
                          {job.job_type || "full_personalization"}
                        </div>
                      </td>

                      <td className="px-4 py-4 text-slate-600">
                        {job.user_email || job.user || "-"}
                      </td>

                      <td className="px-4 py-4">
                        <Badge variant={getStatusVariant(job.status)}>
                          {job.status || "unknown"}
                        </Badge>
                      </td>

                      <td className="px-4 py-4 text-slate-600">
                        {job.completed_items || 0}/{job.total_items || 0}
                      </td>

                      <td className="px-4 py-4 text-slate-600">
                        {job.credits_used || 0}
                      </td>

                      <td className="px-4 py-4 text-slate-500">
                        {formatDate(job.created_at)}
                      </td>
                    </tr>
                  ))}

                  {aiJobs.length === 0 && (
                    <tr>
                      <td
                        colSpan={6}
                        className="px-4 py-10 text-center text-sm text-slate-500"
                      >
                        No AI jobs found.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Users</CardTitle>
            <CardDescription>
              Recent users, access status, and usage summary.
            </CardDescription>
          </CardHeader>

          <CardContent>
            <div className="overflow-x-auto rounded-2xl border border-slate-200">
              <table className="min-w-[1000px] w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                  <tr>
                    <th className="px-4 py-3">User</th>
                    <th className="px-4 py-3">Role</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Searches</th>
                    <th className="px-4 py-3">Leads</th>
                    <th className="px-4 py-3">AI</th>
                    <th className="px-4 py-3">Joined</th>
                    <th className="px-4 py-3 text-right">Action</th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-slate-200 bg-white">
                  {users.slice(0, 15).map((user) => {
                    const name =
                      user.full_name ||
                      `${user.first_name || ""} ${user.last_name || ""}`.trim() ||
                      user.username ||
                      user.email ||
                      `User #${user.id}`;

                    const role = user.is_superuser
                      ? "super admin"
                      : user.is_staff
                        ? "staff"
                        : "user";

                    return (
                      <tr key={user.id} className="hover:bg-slate-50">
                        <td className="px-4 py-4">
                          <div className="font-semibold text-slate-900">
                            {name}
                          </div>
                          <div className="text-xs text-slate-500">
                            {user.email || "-"}
                          </div>
                        </td>

                        <td className="px-4 py-4">
                          <Badge variant={user.is_staff ? "success" : "neutral"}>
                            {role}
                          </Badge>
                        </td>

                        <td className="px-4 py-4">
                          <Badge
                            variant={user.is_active ? "success" : "danger"}
                          >
                            {user.is_active ? "active" : "inactive"}
                          </Badge>
                        </td>

                        <td className="px-4 py-4 text-slate-600">
                          {user.searches_count ?? user.total_searches ?? 0}
                        </td>

                        <td className="px-4 py-4 text-slate-600">
                          {user.leads_count ?? user.total_leads ?? 0}
                        </td>

                        <td className="px-4 py-4">
                          <Badge variant={user.ai_enabled ? "success" : "neutral"}>
                            {user.ai_enabled ? "enabled" : "off"}
                          </Badge>
                        </td>

                        <td className="px-4 py-4 text-slate-500">
                          {formatDate(user.date_joined)}
                        </td>

                        <td className="px-4 py-4 text-right">
                          {user.is_active ? (
                            <Button
                              variant="danger"
                              className="h-9 px-3"
                              disabled={
                                user.is_superuser ||
                                suspendUserMutation.isPending
                              }
                              onClick={() => {
                                if (confirm(`Suspend ${user.email}?`)) {
                                  suspendUserMutation.mutate(user.id);
                                }
                              }}
                            >
                              <UserX className="mr-2 h-4 w-4" />
                              Suspend
                            </Button>
                          ) : (
                            <Button
                              variant="outline"
                              className="h-9 px-3"
                              disabled={activateUserMutation.isPending}
                              onClick={() =>
                                activateUserMutation.mutate(user.id)
                              }
                            >
                              <UserCheck className="mr-2 h-4 w-4" />
                              Activate
                            </Button>
                          )}
                        </td>
                      </tr>
                    );
                  })}

                  {users.length === 0 && (
                    <tr>
                      <td
                        colSpan={8}
                        className="px-4 py-10 text-center text-sm text-slate-500"
                      >
                        No users found.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Monitoring Events</CardTitle>
            <CardDescription>
              Recent backend errors, warnings, and system events.
            </CardDescription>
          </CardHeader>

          <CardContent>
            <div className="space-y-3">
              {events.slice(0, 12).map((event) => {
                const EventIcon = getEventIcon(event);

                return (
                  <div
                    key={event.id}
                    className="rounded-2xl border border-slate-200 bg-white p-4"
                  >
                    <div className="flex items-start gap-3">
                      <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-100">
                        <EventIcon className="h-4 w-4 text-slate-600" />
                      </div>

                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="font-semibold text-slate-900">
                            {event.title || "System Event"}
                          </p>

                          <Badge variant={getEventVariant(event.level)}>
                            {event.level || "info"}
                          </Badge>

                          {event.source && (
                            <Badge variant="neutral">{event.source}</Badge>
                          )}
                        </div>

                        {event.message && (
                          <p className="mt-2 line-clamp-3 text-sm leading-6 text-slate-600">
                            {event.message}
                          </p>
                        )}

                        <p className="mt-2 text-xs text-slate-500">
                          {formatDate(event.created_at)}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}

              {events.length === 0 && (
                <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-10 text-center">
                  <CheckCircle2 className="mx-auto h-8 w-8 text-green-500" />
                  <h3 className="mt-3 font-semibold text-slate-800">
                    No monitoring events
                  </h3>
                  <p className="mt-1 text-sm text-slate-500">
                    System looks clean.
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Searches</CardTitle>
          <CardDescription>
            Latest platform searches across all users.
          </CardDescription>
        </CardHeader>

        <CardContent>
          <div className="overflow-x-auto rounded-2xl border border-slate-200">
            <table className="min-w-[1000px] w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-3">Search</th>
                  <th className="px-4 py-3">User</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Progress</th>
                  <th className="px-4 py-3">Leads</th>
                  <th className="px-4 py-3">Created</th>
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-200 bg-white">
                {searches.slice(0, 15).map((search) => (
                  <tr key={search.id} className="hover:bg-slate-50">
                    <td className="px-4 py-4">
                      <div className="font-semibold text-slate-900">
                        Search #{search.id}
                      </div>
                      <div className="text-xs text-slate-500">
                        {(search.keywords || []).join(", ")} in{" "}
                        {(search.locations || []).join(", ")}
                      </div>
                    </td>

                    <td className="px-4 py-4 text-slate-600">
                      {search.user_email || search.user_id || "-"}
                    </td>

                    <td className="px-4 py-4">
                      <Badge variant={getStatusVariant(search.status)}>
                        {search.status || "unknown"}
                      </Badge>
                    </td>

                    <td className="px-4 py-4 text-slate-600">
                      {search.completed_tasks || 0}/{search.total_tasks || 0}
                    </td>

                    <td className="px-4 py-4 text-slate-600">
                      {search.leads_count || 0}
                    </td>

                    <td className="px-4 py-4 text-slate-500">
                      {formatDate(search.created_at)}
                    </td>
                  </tr>
                ))}

                {searches.length === 0 && (
                  <tr>
                    <td
                      colSpan={6}
                      className="px-4 py-10 text-center text-sm text-slate-500"
                    >
                      No searches found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}