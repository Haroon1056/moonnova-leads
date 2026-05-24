export type AiJobStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export type AiJobType =
  | "lead_insight"
  | "full_personalization"
  | "summary"
  | "email"
  | "social_message"
  | string;

export type OutreachChannel =
  | "email"
  | "facebook"
  | "linkedin"
  | "whatsapp"
  | "multi_channel";

export interface AiUsage {
  credits_total?: number;
  credits_used?: number;
  credits_remaining?: number;
  monthly_limit?: number;
  used_this_month?: number;
  remaining_this_month?: number;
  plan_name?: string;
  ai_enabled?: boolean;
  model?: string;
  reset_at?: string | null;
}

export interface AiInsight {
  id?: number;
  lead?: number;
  lead_name?: string;

  target_offer?: string | null;
  campaign_goal?: string | null;
  tone?: string | null;
  target_audience?: string | null;
  outreach_channel?: string | null;
  custom_instructions?: string | null;

  ai_priority?: string | null;
  priority?: string | null;

  ai_summary?: string | null;

  ai_suggested_offer?: string | null;
  suggested_offer?: string | null;

  ai_offer_reason?: string | null;
  offer_reason?: string | null;

  ai_best_channel?: string | null;
  best_outreach_channel?: string | null;

  ai_channel_reason?: string | null;
  channel_reason?: string | null;

  ai_first_line?: string | null;
  first_line?: string | null;

  ai_email_subject?: string | null;
  email_subject?: string | null;

  ai_email_body?: string | null;
  email_body?: string | null;

  ai_followup_1?: string | null;
  follow_up_1?: string | null;

  ai_followup_2?: string | null;
  follow_up_2?: string | null;

  ai_followup_3?: string | null;
  follow_up_3?: string | null;

  ai_facebook_message?: string | null;
  facebook_message?: string | null;

  ai_linkedin_message?: string | null;
  linkedin_message?: string | null;

  ai_whatsapp_message?: string | null;
  whatsapp_message?: string | null;

  ai_website_weakness?: string | null;
  website_weakness?: string | null;

  ai_local_seo_opportunity?: string | null;
  local_seo_opportunity?: string | null;

  ai_score_explanation?: string | null;
  opportunity_reason?: string | null;

  provider?: string | null;
  model_name?: string | null;

  raw_response?: Record<string, unknown>;
  generated_data?: Record<string, unknown>;
  data?: Record<string, unknown>;
  result?: Record<string, unknown>;

  generated_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface AiJob {
  id: number;
  user?: number;

  job_type: AiJobType;
  status: AiJobStatus | string;

  lead_ids?: number[];

  total_items: number;
  completed_items: number;
  failed_items: number;
  skipped_items?: number;
  processed_items?: number;

  credit_cost?: number;
  credits_used?: number;

  progress?: number;
  is_finished?: boolean;

  target_offer?: string | null;
  campaign_goal?: string | null;
  tone?: string | null;
  target_audience?: string | null;
  outreach_channel?: OutreachChannel | string | null;
  custom_instructions?: string | null;

  error_message?: string | null;

  started_at?: string | null;
  completed_at?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface AiJobListResponse {
  count?: number;
  next?: string | null;
  previous?: string | null;
  results?: AiJob[];
}

export interface BulkAiPayload {
  lead_ids?: number[];
  search_id?: number;
  list_id?: number;

  job_type: AiJobType;
  force?: boolean;

  target_offer?: string;
  campaign_goal?: string;
  tone?: string;
  target_audience?: string;
  outreach_channel?: OutreachChannel | string;
  custom_instructions?: string;
}

export interface SingleAiPayload {
  job_type?: AiJobType;
  force?: boolean;

  target_offer?: string;
  campaign_goal?: string;
  tone?: string;
  target_audience?: string;
  outreach_channel?: OutreachChannel | string;
  custom_instructions?: string;
}