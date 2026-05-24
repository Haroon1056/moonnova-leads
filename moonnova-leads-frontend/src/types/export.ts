export type ExportStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export type ExportFormat = "csv" | "xlsx";

export type ExportScope =
  | "all_leads"
  | "search"
  | "lead_list"
  | "selected_leads"
  | "filtered";

export interface ExportHistory {
  id: number;
  user?: number;

  export_type?: ExportFormat;
  file_format?: ExportFormat;

  export_scope?: ExportScope | string;

  status: ExportStatus | string;

  search?: number | null;
  lead_list?: number | null;
  lead_ids?: number[];

  include_basic_fields?: boolean;
  include_contact_fields?: boolean;
  include_website_fields?: boolean;
  include_enrichment_fields?: boolean;
  include_ai_fields?: boolean;
  include_raw_data?: boolean;

  filters?: Record<string, unknown>;

  file?: string | null;
  file_url?: string | null;
  download_url?: string | null;
  file_name?: string | null;
  file_size?: number | null;

  total_rows?: number;
  error_message?: string | null;

  started_at?: string | null;
  completed_at?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface ExportHistoryListResponse {
  count?: number;
  next?: string | null;
  previous?: string | null;
  results?: ExportHistory[];
}

export interface CreateExportPayload {
  export_type?: ExportFormat;
  file_format?: ExportFormat;
  export_scope: ExportScope | string;

  search?: number | null;
  search_id?: number | null;

  lead_list?: number | null;
  lead_list_id?: number | null;

  lead_ids?: number[];

  include_basic_fields?: boolean;
  include_contact_fields?: boolean;
  include_website_fields?: boolean;
  include_enrichment_fields?: boolean;
  include_ai_fields?: boolean;
  include_raw_data?: boolean;

  filters?: Record<string, unknown>;
}