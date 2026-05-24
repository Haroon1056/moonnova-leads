import { api } from "@/lib/api";
import type { Lead, LeadFilters, LeadListResponse } from "@/types/lead";
import type {
  SavedLeadList,
  LeadListCollectionResponse
} from "@/types/lead-list";

function cleanParams(filters: LeadFilters) {
  const params: Record<string, unknown> = {};

  const backendKeyMap: Record<string, string> = {
    search: "q",
    no_website: "has_website",
    broken_website: "is_broken_website",
    min_lead_score: "min_score",
    min_rating: "rating"
  };

  Object.entries(filters).forEach(([key, value]) => {
    if (value === "" || value === undefined || value === null) return;

    const backendKey = backendKeyMap[key] || key;

    if (key === "no_website") {
      params[backendKey] = value === true ? false : value;
      return;
    }

    params[backendKey] = value;
  });

  return params;
}

function normalizeLeadList(data: LeadListResponse | Lead[]): LeadListResponse {
  if (Array.isArray(data)) {
    return {
      results: data,
      count: data.length,
      next: null,
      previous: null
    };
  }

  return data;
}

function normalizeSavedLists(
  data: LeadListCollectionResponse | SavedLeadList[]
): SavedLeadList[] {
  if (Array.isArray(data)) return data;
  return data.results || [];
}

function normalizeSavedLeadList(data: SavedLeadList | any): SavedLeadList {
  if (data?.lead_list) return data.lead_list;
  if (data?.list) return data.list;
  return data;
}

export const leadService = {
  async getLeads(filters: LeadFilters) {
    const response = await api.get<LeadListResponse | Lead[]>("/leads/", {
      params: cleanParams(filters)
    });

    return normalizeLeadList(response.data);
  },

  async getLead(id: number | string) {
    const response = await api.get<Lead>(`/leads/${id}/`);
    return response.data;
  },

  async updateLead(id: number | string, payload: Partial<Lead>) {
    const response = await api.patch<Lead>(`/leads/${id}/`, payload);
    return response.data;
  },

  async enrichLead(id: number | string) {
    const response = await api.post(`/leads/${id}/enrich-website/`, {
      force: false
    });

    return response.data;
  },

  async bulkEnrichLeadWebsites(leadIds: number[]) {
    const response = await api.post("/leads/bulk-enrich-website/", {
      lead_ids: leadIds,
      force: false
    });

    return response.data;
  },

  async bulkAction(
    action: string,
    leadIds: number[],
    extra?: Record<string, unknown>
  ) {
    const response = await api.post("/leads/bulk-action/", {
      action,
      lead_ids: leadIds,
      ...extra
    });

    return response.data;
  },

  async markFavorite(leadIds: number[]) {
    return this.bulkAction("favorite", leadIds);
  },

  async unmarkFavorite(leadIds: number[]) {
    return this.bulkAction("unfavorite", leadIds);
  },

  async deleteLeads(leadIds: number[]) {
    return this.bulkAction("delete", leadIds);
  },

  async getLeadLists() {
    const response = await api.get<LeadListCollectionResponse | SavedLeadList[]>(
      "/leads/lists/"
    );

    return normalizeSavedLists(response.data);
  },

  async getLeadList(id: number | string) {
    const response = await api.get<SavedLeadList | any>(`/leads/lists/${id}/`);
    return normalizeSavedLeadList(response.data);
  },

  async createLeadList(payload: {
    name: string;
    description?: string;
  }) {
    const response = await api.post<SavedLeadList>("/leads/lists/", payload);
    return response.data;
  },

  async addLeadsToList(listId: number | string, leadIds: number[]) {
    const response = await api.post(`/leads/lists/${listId}/add/`, {
      lead_ids: leadIds
    });

    return response.data;
  }
};