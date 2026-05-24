import {
  Copy,
  ExternalLink,
  Globe,
  Mail,
  MapPin,
  Phone,
  Star,
  X
} from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Lead } from "@/types/lead";
import { formatDate } from "@/lib/utils";

interface LeadDetailDrawerProps {
  lead: Lead | null;
  open: boolean;
  onClose: () => void;
  onEnrich: (leadId: number) => void;
  onFavorite: (leadId: number) => void;
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

function getWebsiteStatusVariant(status?: string | null) {
  if (!status || status === "unknown") return "neutral";
  if (status === "working") return "success";
  if (status === "no_website") return "warning";

  if (
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
    ].includes(status)
  ) {
    return "danger";
  }

  return "neutral";
}

function formatStatus(value?: string | null) {
  if (!value) return "Unknown";
  return value.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function copyToClipboard(value?: string | null) {
  if (!value) return;

  navigator.clipboard.writeText(value);
  toast.success("Copied");
}

export function LeadDetailDrawer({
  lead,
  open,
  onClose,
  onEnrich,
  onFavorite
}: LeadDetailDrawerProps) {
  if (!open || !lead) return null;

  const email = getLeadEmail(lead);
  const website = lead.website || lead.website_url;

  return (
    <div className="fixed inset-0 z-50">
      <button
        className="absolute inset-0 bg-slate-900/40"
        onClick={onClose}
      />

      <aside className="absolute right-0 top-0 h-full w-full max-w-xl overflow-y-auto bg-white shadow-2xl">
        <div className="sticky top-0 z-10 border-b border-slate-200 bg-white px-6 py-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="text-xl font-bold text-slate-950">
                {getLeadName(lead)}
              </h3>
              <p className="mt-1 text-sm text-slate-500">
                {lead.category || "Business Lead"}
              </p>
            </div>

            <button
              onClick={onClose}
              className="rounded-xl border border-slate-200 p-2 hover:bg-slate-50"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        <div className="space-y-6 p-6">
          <div className="flex flex-wrap gap-2">
            <Badge variant={getWebsiteStatusVariant(lead.website_status)}>
              {formatStatus(lead.website_status)}
            </Badge>

            <Badge variant="neutral">
              Enrichment: {formatStatus(lead.enrichment_status || "not_started")}
            </Badge>

            {lead.is_favorite && (
              <Badge variant="warning">
                <Star className="mr-1 h-3 w-3" />
                Favorite
              </Badge>
            )}
          </div>

          <div className="grid gap-3">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-medium uppercase text-slate-500">
                Contact
              </p>

              <div className="mt-3 space-y-3">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2 text-sm text-slate-700">
                    <Phone className="h-4 w-4 text-slate-400" />
                    {lead.phone || "-"}
                  </div>

                  {lead.phone && (
                    <Button
                      variant="ghost"
                      className="h-8 px-2"
                      onClick={() => copyToClipboard(lead.phone)}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                  )}
                </div>

                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2 text-sm text-slate-700">
                    <Mail className="h-4 w-4 text-slate-400" />
                    {email || "-"}
                  </div>

                  {email && (
                    <Button
                      variant="ghost"
                      className="h-8 px-2"
                      onClick={() => copyToClipboard(email)}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                  )}
                </div>

                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2 text-sm text-slate-700">
                    <Globe className="h-4 w-4 text-slate-400" />
                    <span className="truncate">{website || "-"}</span>
                  </div>

                  {website && (
                    <a
                      href={website}
                      target="_blank"
                      rel="noreferrer"
                      className="rounded-lg p-2 text-primary hover:bg-slate-100"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  )}
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-medium uppercase text-slate-500">
                Location
              </p>

              <div className="mt-3 flex gap-2 text-sm text-slate-700">
                <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />
                <div>
                  <p>{lead.address || "-"}</p>
                  <p className="mt-1 text-slate-500">{getLeadLocation(lead)}</p>
                </div>
              </div>
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-2xl border border-slate-200 bg-white p-4">
                <p className="text-xs text-slate-500">Rating</p>
                <p className="mt-1 text-2xl font-bold">
                  {lead.rating || "-"}
                </p>
              </div>

              <div className="rounded-2xl border border-slate-200 bg-white p-4">
                <p className="text-xs text-slate-500">Reviews</p>
                <p className="mt-1 text-2xl font-bold">
                  {lead.review_count || lead.rating_count || "-"}
                </p>
              </div>

              <div className="rounded-2xl border border-slate-200 bg-white p-4">
                <p className="text-xs text-slate-500">Lead Score</p>
                <p className="mt-1 text-2xl font-bold">
                  {lead.lead_score ?? 0}
                </p>
              </div>

              <div className="rounded-2xl border border-slate-200 bg-white p-4">
                <p className="text-xs text-slate-500">Opportunity</p>
                <p className="mt-1 text-2xl font-bold">
                  {lead.opportunity_score ?? 0}
                </p>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-medium uppercase text-slate-500">
                Website Details
              </p>

              <div className="mt-3 grid gap-2 text-sm">
                <div className="flex justify-between gap-3">
                  <span className="text-slate-500">Status</span>
                  <span className="font-medium text-slate-800">
                    {formatStatus(lead.website_status)}
                  </span>
                </div>

                <div className="flex justify-between gap-3">
                  <span className="text-slate-500">HTTP</span>
                  <span className="font-medium text-slate-800">
                    {lead.website_http_status || "-"}
                  </span>
                </div>

                <div className="flex justify-between gap-3">
                  <span className="text-slate-500">Platform</span>
                  <span className="font-medium text-slate-800">
                    {lead.website_platform || "-"}
                  </span>
                </div>

                <div className="flex justify-between gap-3">
                  <span className="text-slate-500">Email Confidence</span>
                  <span className="font-medium text-slate-800">
                    {lead.email_confidence ?? 0}%
                  </span>
                </div>
              </div>
            </div>

            {lead.opportunity_reason && (
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-xs font-medium uppercase text-slate-500">
                  Opportunity Reason
                </p>
                <p className="mt-2 text-sm leading-6 text-slate-700">
                  {lead.opportunity_reason}
                </p>
              </div>
            )}

            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-medium uppercase text-slate-500">
                Source
              </p>

              <p className="mt-2 text-sm text-slate-700">
                {lead.source_query ||
                  `${lead.source_keyword || lead.keyword || "-"} in ${
                    lead.source_location || lead.location || "-"
                  }`}
              </p>

              <p className="mt-2 text-xs text-slate-500">
                Added {formatDate(lead.created_at)}
              </p>
            </div>

            <div className="flex flex-wrap gap-3">
              <Button onClick={() => onEnrich(lead.id)}>
                Start Enrichment
              </Button>

              <Button
                variant="outline"
                onClick={() => onFavorite(lead.id)}
              >
                <Star className="mr-2 h-4 w-4" />
                Favorite
              </Button>

              {lead.map_link && (
                <a href={lead.map_link} target="_blank" rel="noreferrer">
                  <Button variant="outline">
                    Open Map
                    <ExternalLink className="ml-2 h-4 w-4" />
                  </Button>
                </a>
              )}
            </div>
          </div>
        </div>
      </aside>
    </div>
  );
}