import type { Lead } from "@/types/lead";

export interface SavedLeadList {
  id: number;
  name: string;
  description?: string | null;
  leads_count?: number;
  leads?: Lead[];
  created_at?: string;
  updated_at?: string;
}

export interface LeadListCollectionResponse {
  count?: number;
  next?: string | null;
  previous?: string | null;
  results?: SavedLeadList[];
}