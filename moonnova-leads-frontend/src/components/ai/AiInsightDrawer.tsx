import {
  Brain,
  Copy,
  Loader2,
  MessageCircle,
  RefreshCw,
  Target,
  X
} from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { AiInsight, SingleAiPayload } from "@/types/ai";
import type { Lead } from "@/types/lead";
import { useLeadAiInsight } from "@/hooks/useAI";

interface AiInsightDrawerProps {
  lead: Lead | null;
  open: boolean;
  onClose: () => void;
}

function getLeadName(lead: Lead) {
  return lead.name || lead.business_name || "Unnamed Business";
}

function copyText(value?: string | null) {
  if (!value) return;

  navigator.clipboard.writeText(value);
  toast.success("Copied");
}

function pick(...values: any[]) {
  return values.find(
    (value) =>
      value !== undefined &&
      value !== null &&
      String(value).trim() !== ""
  );
}

function getInsightData(insight?: any) {
  return {
    ...(insight || {}),
    ...((insight as any)?.generated_data || {}),
    ...((insight as any)?.data || {}),
    ...((insight as any)?.result || {}),
    ...((insight as any)?.raw_response || {})
  };
}

function getPriority(insight: any) {
  return pick(insight?.priority, insight?.ai_priority);
}

function getSummary(insight: any) {
  return pick(
    insight?.ai_summary,
    insight?.summary,
    insight?.lead_summary,
    insight?.business_summary
  );
}

function getSuggestedOffer(insight: any) {
  return pick(
    insight?.suggested_offer,
    insight?.ai_suggested_offer,
    insight?.offer,
    insight?.recommended_offer,
    insight?.target_offer
  );
}

function getBestChannel(insight: any) {
  return pick(
    insight?.best_outreach_channel,
    insight?.ai_best_channel,
    insight?.best_channel
  );
}

function getOfferReason(insight: any) {
  return pick(insight?.offer_reason, insight?.ai_offer_reason);
}

function getChannelReason(insight: any) {
  return pick(insight?.channel_reason, insight?.ai_channel_reason);
}

function getFirstLine(insight: any) {
  return pick(insight?.first_line, insight?.ai_first_line);
}

function getSubject(insight: any) {
  return pick(
    insight?.email_subject,
    insight?.ai_email_subject,
    insight?.subject,
    insight?.subject_line
  );
}

function getEmailBody(insight: any) {
  return pick(
    insight?.email_body,
    insight?.ai_email_body,
    insight?.email,
    insight?.personalized_email,
    insight?.message
  );
}

function getFollowUp1(insight: any) {
  return pick(insight?.follow_up_1, insight?.ai_followup_1);
}

function getFollowUp2(insight: any) {
  return pick(insight?.follow_up_2, insight?.ai_followup_2);
}

function getFollowUp3(insight: any) {
  return pick(insight?.follow_up_3, insight?.ai_followup_3);
}

function getFacebookMessage(insight: any) {
  return pick(
    insight?.facebook_message,
    insight?.ai_facebook_message,
    insight?.social_message,
    insight?.fb_message
  );
}

function getLinkedinMessage(insight: any) {
  return pick(
    insight?.linkedin_message,
    insight?.ai_linkedin_message,
    insight?.linkedin_dm
  );
}

function getWhatsappMessage(insight: any) {
  return pick(
    insight?.whatsapp_message,
    insight?.ai_whatsapp_message,
    insight?.whatsapp_text,
    insight?.chat_message
  );
}

function getWebsiteWeakness(insight: any) {
  return pick(insight?.website_weakness, insight?.ai_website_weakness);
}

function getLocalSeoOpportunity(insight: any) {
  return pick(
    insight?.local_seo_opportunity,
    insight?.ai_local_seo_opportunity
  );
}

function getOpportunityReason(insight: any) {
  return pick(
    insight?.opportunity_reason,
    insight?.ai_score_explanation,
    insight?.score_explanation
  );
}

function Section({
  title,
  children,
  action
}: {
  title: string;
  children: React.ReactNode;
  action?: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <p className="text-sm font-semibold text-slate-800">{title}</p>
        {action}
      </div>
      {children}
    </div>
  );
}

function MessageBlock({
  label,
  value
}: {
  label: string;
  value?: string | null;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-3">
      <div className="mb-2 flex items-center justify-between gap-3">
        <p className="text-xs font-semibold uppercase text-slate-500">
          {label}
        </p>

        {value && (
          <Button
            variant="ghost"
            className="h-8 px-2"
            onClick={() => copyText(value)}
          >
            <Copy className="h-4 w-4" />
          </Button>
        )}
      </div>

      <p className="whitespace-pre-wrap text-sm leading-6 text-slate-700">
        {value || "Not generated yet."}
      </p>
    </div>
  );
}

export function AiInsightDrawer({
  lead,
  open,
  onClose
}: AiInsightDrawerProps) {
  const leadId = lead?.id;
  const { insightQuery, generateInsightMutation } = useLeadAiInsight(leadId);

  if (!open || !lead) return null;

  const insight = insightQuery.data as AiInsight | undefined;
  const insightData = getInsightData(insight);

  const defaultPayload: SingleAiPayload = {
    job_type: "full_personalization",
    force: true,
    tone: "friendly, simple, natural, practical, not too salesy",
    outreach_channel: "email",
    target_audience: "local business owner",
    custom_instructions:
      "Generate complete outreach fields including subject, email body, follow-ups, Facebook, LinkedIn, and WhatsApp messages."
  };

  const priority = getPriority(insightData);
  const bestChannel = getBestChannel(insightData);
  const suggestedOffer = getSuggestedOffer(insightData);
  const summary = getSummary(insightData);

  return (
    <div className="fixed inset-0 z-50">
      <button
        className="absolute inset-0 bg-slate-900/40"
        onClick={onClose}
      />

      <aside className="absolute right-0 top-0 h-full w-full max-w-2xl overflow-y-auto bg-white shadow-2xl">
        <div className="sticky top-0 z-10 border-b border-slate-200 bg-white px-6 py-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <Brain className="h-5 w-5 text-primary" />
                <h3 className="text-xl font-bold text-slate-950">
                  AI Insight
                </h3>
              </div>

              <p className="mt-1 text-sm text-slate-500">
                {getLeadName(lead)}
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

        <div className="space-y-5 p-6">
          {insightQuery.isLoading ? (
            <div className="flex min-h-[220px] items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
            </div>
          ) : (
            <>
              <div className="flex flex-wrap gap-2">
                <Badge>
                  Priority: {priority || "Not set"}
                </Badge>

                <Badge variant="neutral">
                  Channel: {bestChannel || "Not set"}
                </Badge>

                {suggestedOffer && (
                  <Badge variant="success">Offer Ready</Badge>
                )}
              </div>

              <div className="flex flex-wrap gap-2">
                <Button
                  onClick={() =>
                    generateInsightMutation.mutate(defaultPayload)
                  }
                  disabled={generateInsightMutation.isPending}
                >
                  {generateInsightMutation.isPending ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <RefreshCw className="mr-2 h-4 w-4" />
                  )}
                  Generate / Regenerate
                </Button>
              </div>

              <Section
                title="AI Summary"
                action={
                  summary ? (
                    <Button
                      variant="ghost"
                      className="h-8 px-2"
                      onClick={() => copyText(summary)}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                  ) : null
                }
              >
                <p className="whitespace-pre-wrap text-sm leading-6 text-slate-700">
                  {summary || "No summary generated yet."}
                </p>
              </Section>

              <Section title="Suggested Offer">
                <div className="flex gap-3">
                  <Target className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                  <div>
                    <p className="text-sm leading-6 text-slate-700">
                      {suggestedOffer || "No suggested offer generated yet."}
                    </p>

                    {getOfferReason(insightData) && (
                      <p className="mt-2 text-xs leading-5 text-slate-500">
                        {getOfferReason(insightData)}
                      </p>
                    )}
                  </div>
                </div>
              </Section>

              <Section title="Best Outreach Channel">
                <div className="grid gap-3">
                  <MessageBlock
                    label="Best Channel"
                    value={bestChannel}
                  />
                  <MessageBlock
                    label="Channel Reason"
                    value={getChannelReason(insightData)}
                  />
                </div>
              </Section>

              <Section title="Opportunity">
                <div className="grid gap-3">
                  <MessageBlock
                    label="Website Weakness"
                    value={getWebsiteWeakness(insightData)}
                  />
                  <MessageBlock
                    label="Local SEO Opportunity"
                    value={getLocalSeoOpportunity(insightData)}
                  />
                  <MessageBlock
                    label="Opportunity Reason"
                    value={getOpportunityReason(insightData)}
                  />
                </div>
              </Section>

              <Section title="Email Outreach">
                <div className="grid gap-3">
                  <MessageBlock
                    label="First Line"
                    value={getFirstLine(insightData)}
                  />

                  <MessageBlock
                    label="Subject"
                    value={getSubject(insightData)}
                  />

                  <MessageBlock
                    label="Email Body"
                    value={getEmailBody(insightData)}
                  />

                  <MessageBlock
                    label="Follow-up 1"
                    value={getFollowUp1(insightData)}
                  />

                  <MessageBlock
                    label="Follow-up 2"
                    value={getFollowUp2(insightData)}
                  />

                  <MessageBlock
                    label="Follow-up 3"
                    value={getFollowUp3(insightData)}
                  />
                </div>
              </Section>

              <Section title="Social / Chat Messages">
                <div className="grid gap-3">
                  <MessageBlock
                    label="Facebook Message"
                    value={getFacebookMessage(insightData)}
                  />

                  <MessageBlock
                    label="LinkedIn Message"
                    value={getLinkedinMessage(insightData)}
                  />

                  <MessageBlock
                    label="WhatsApp Message"
                    value={getWhatsappMessage(insightData)}
                  />
                </div>
              </Section>

              <div className="rounded-2xl border border-indigo-200 bg-indigo-50 p-4 text-sm text-indigo-700">
                <div className="flex gap-2">
                  <MessageCircle className="mt-0.5 h-4 w-4 shrink-0" />
                  <p>
                    Use the copy buttons to move AI messages into email,
                    LinkedIn, Facebook, or WhatsApp outreach.
                  </p>
                </div>
              </div>
            </>
          )}
        </div>
      </aside>
    </div>
  );
}