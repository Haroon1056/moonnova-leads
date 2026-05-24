export interface AdminOverview {
  period_days?: number;

  users_total?: number;
  active_users?: number;
  staff_users?: number;

  searches_total?: number;
  running_searches?: number;
  completed_searches?: number;
  failed_searches?: number;
  cancelled_searches?: number;

  leads_total?: number;

  exports_total?: number;

  ai_jobs_total?: number;
  ai_jobs_running?: number;
  ai_jobs_failed?: number;
  ai_credits_used_total?: number;

  system_status?: string;

  users?: {
    total?: number;
    active?: number;
    staff?: number;
  };

  searches?: {
    total?: number;
    running?: number;
    completed?: number;
    failed?: number;
    cancelled?: number;
    last_period?: number;
  };

  leads?: {
    total?: number;
    last_period?: number;
  };

  exports?: {
    total?: number;
    completed?: number;
    failed?: number;
    last_period?: number;
  };

  enrichment?: {
    total_jobs?: number;
    running_jobs?: number;
    failed_jobs?: number;
  };
}

export interface AdminUser {
  id: number;
  email?: string;
  username?: string;
  full_name?: string;
  first_name?: string;
  last_name?: string;

  is_active?: boolean;
  is_staff?: boolean;
  is_superuser?: boolean;
  is_verified?: boolean;

  auth_provider?: string;

  date_joined?: string;
  last_login?: string | null;

  account_status?: string;
  beta_access?: boolean;
  ai_enabled?: boolean;
  plan_name?: string;

  searches_count?: number;
  leads_count?: number;
  exports_count?: number;
  ai_jobs_count?: number;

  total_searches?: number;
  total_leads?: number;
  total_exports?: number;
}

export interface PaginatedResponse<T> {
  count?: number;
  next?: string | null;
  previous?: string | null;
  results?: T[];
}

export interface SystemHealth {
  status?: string;
  database?: string;
  redis?: string;
  cache?: string;
  celery?: string;

  scraper_worker?: string;
  enrichment_worker?: string;
  default_worker?: string;

  storage?: string;
  ai_provider?: string;

  worker_names?: string[];

  stuck_searches?: number;
  stuck_enrichment_jobs?: number;

  failed_searches_24h?: number;
  failed_exports_24h?: number;
  failed_ai_jobs_24h?: number;

  checked_at?: string;
}

export interface MonitoringEvent {
  id: number;
  user?: number | null;
  user_email?: string | null;

  level?: string;
  source?: string;
  title?: string;
  message?: string;

  task_name?: string | null;
  task_id?: string | null;

  object_type?: string | null;
  object_id?: number | string | null;

  metadata?: Record<string, unknown>;

  resolved?: boolean;
  resolved_at?: string | null;

  created_at?: string;
}

export interface AdminAiSummary {
  ai_enabled?: boolean;
  provider?: string | null;
  model?: string | null;

  jobs_total?: number;
  jobs_running?: number;
  jobs_completed?: number;
  jobs_failed?: number;

  credits_used_total?: number;
  credits_used_this_month?: number;

  quota_errors?: number;
  last_error?: string | null;
}

export interface AdminAiJob {
  id: number;
  user?: number;
  user_email?: string;

  job_type?: string;
  status?: string;

  total_items?: number;
  completed_items?: number;
  failed_items?: number;
  skipped_items?: number;

  credits_used?: number;

  error_message?: string | null;

  created_at?: string;
  updated_at?: string;
  completed_at?: string | null;
}

export interface AdminSearch {
  id: number;
  user_id?: number;
  user_email?: string;

  keywords?: string[];
  locations?: string[];

  status?: string;
  max_leads?: number;
  scrape_mode?: string;
  email_enrichment?: boolean;

  total_tasks?: number;
  completed_tasks?: number;
  failed_tasks?: number;

  progress?: number;
  leads_count?: number;

  error_message?: string | null;

  created_at?: string;
  updated_at?: string;
}