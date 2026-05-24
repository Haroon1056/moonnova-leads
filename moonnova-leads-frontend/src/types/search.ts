export type SearchStatus =
  | "pending"
  | "running"
  | "paused"
  | "completed"
  | "failed"
  | "cancelled";

export type ScrapeMode = "safe" | "balanced" | "deep";

export interface CreateSearchPayload {
  keywords: string[];
  locations: string[];
  max_leads?: number;
  scrape_mode?: ScrapeMode;
  email_enrichment?: boolean;
}

export interface SearchQueryTask {
  id: number;
  keyword: string;
  location: string;
  query_text?: string;
  status: string;
  max_leads?: number;
  leads_found?: number;
  processed_index?: number;
  retry_count?: number;
  max_retries?: number;
  error_message?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface SearchJob {
  id: number;
  user?: number;

  keywords?: string[];
  locations?: string[];

  keyword?: string;
  location?: string;

  status: SearchStatus | string;
  scrape_mode?: ScrapeMode;

  max_leads?: number;
  email_enrichment?: boolean;

  total_tasks?: number;
  completed_tasks?: number;
  failed_tasks?: number;

  leads_count?: number;
  leads_count_db?: number;

  progress?: number;

  error_message?: string | null;

  query_tasks?: SearchQueryTask[];

  created_at?: string;
  updated_at?: string;
  started_at?: string | null;
  completed_at?: string | null;
}

export interface SearchListResponse {
  count?: number;
  next?: string | null;
  previous?: string | null;
  results?: SearchJob[];
}

export interface CreateSearchResponse {
  message: string;
  search_id: number;
  status: string;
  email_enrichment?: boolean;
  usage?: {
    remaining_searches_today?: number;
    remaining_leads_this_month?: number;
  };
  search: SearchJob;
}

export interface SearchProgressEvent {
  search_id: number;
  status?: SearchStatus | string;
  progress?: number;
  total_leads?: number;
  leads_count?: number;
  completed_leads?: number;
  completed_tasks?: number;
  total_tasks?: number;
  message?: string;
}