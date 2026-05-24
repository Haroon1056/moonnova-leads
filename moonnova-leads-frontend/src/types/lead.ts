export interface Lead {
  id: number;
  search: number;

  name?: string;
  business_name?: string;

  keyword?: string | null;
  location?: string | null;
  category?: string | null;

  phone?: string | null;

  email?: string | null;
  email_1?: string | null;
  email_2?: string | null;
  email_3?: string | null;
  email_confidence?: number | null;

  website?: string | null;
  website_url?: string | null;
  domain?: string | null;
  has_website?: boolean;

  website_status?: string | null;
  website_http_status?: number | null;
  website_error?: string | null;
  website_platform?: string | null;

  is_social_only?: boolean;
  is_free_builder?: boolean;
  is_broken_website?: boolean;

  facebook_url?: string | null;
  instagram_url?: string | null;
  linkedin_url?: string | null;
  youtube_url?: string | null;
  tiktok_url?: string | null;

  address?: string | null;
  city?: string | null;
  state?: string | null;
  pincode?: string | null;
  country?: string | null;

  latitude?: string | number | null;
  longitude?: string | number | null;

  rating?: number | string | null;
  rating_count?: number | null;
  review_count?: number | null;

  map_link?: string | null;
  place_id?: string | null;

  status?: "hot" | "warm" | "cold" | string;

  lead_score?: number | null;
  opportunity_score?: number | null;
  opportunity_reason?: string | null;

  tags?: string[];
  notes?: string | null;
  is_favorite?: boolean;

  source_query?: string | null;
  source_keyword?: string | null;
  source_location?: string | null;

  enrichment_status?: string | null;
  enrichment_attempts?: number;
  enrichment_error?: string | null;
  enrichment_last_run_at?: string | null;

  ai_priority?: string | null;
  suggested_offer?: string | null;

  raw_data?: Record<string, unknown>;

  created_at?: string;
  updated_at?: string;
}

export interface LeadListResponse {
  count?: number;
  next?: string | null;
  previous?: string | null;
  results?: Lead[];
}

export interface LeadFilters {
  search?: string;
  keyword?: string;
  location?: string;
  category?: string;
  has_email?: boolean | "";
  has_website?: boolean | "";
  no_website?: boolean | "";
  broken_website?: boolean | "";
  website_status?: string;
  enrichment_status?: string;
  ai_priority?: string;
  is_favorite?: boolean | "";
  min_lead_score?: string;
  min_rating?: string;
  page?: number;
  page_size?: number;
}