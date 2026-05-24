export interface UsageSummary {
  account_status?: string;
  beta_access?: boolean;

  searches_today?: number;
  searches_this_month?: number;
  max_searches_per_day?: number;
  max_searches_per_month?: number;
  remaining_searches_today?: number | null;

  leads_today?: number;
  leads_this_month?: number;
  max_leads_per_day?: number;
  max_leads_per_month?: number;
  max_leads_per_search?: number;
  remaining_leads_this_month?: number | null;

  exports_today?: number;
  exports_this_month?: number;
  max_exports_per_day?: number;
  max_exports_per_month?: number;
  remaining_exports_today?: number | null;

  lead_retention_days?: number;
  search_history_retention_days?: number;
  raw_data_retention_days?: number;
  export_retention_days?: number;

  auto_delete_old_leads?: boolean;
  auto_clear_raw_data?: boolean;
  auto_delete_old_exports?: boolean;

  unlimited_searches?: boolean;
  unlimited_leads?: boolean;
  unlimited_exports?: boolean;
}
