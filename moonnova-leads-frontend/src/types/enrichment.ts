export type EnrichmentJobStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export interface EnrichmentJob {
  id: number;
  user?: number;
  search?: number | null;

  job_type?: string;
  status: EnrichmentJobStatus | string;

  lead_ids?: number[];

  total_items: number;
  completed_items: number;
  failed_items: number;
  skipped_items: number;

  progress?: number;

  error_message?: string | null;

  started_at?: string | null;
  completed_at?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface EnrichmentJobListResponse {
  count?: number;
  next?: string | null;
  previous?: string | null;
  results?: EnrichmentJob[];
}