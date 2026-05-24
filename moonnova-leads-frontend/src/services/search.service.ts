import { api } from "@/lib/api";
import type {
  CreateSearchPayload,
  CreateSearchResponse,
  SearchJob,
  SearchListResponse
} from "@/types/search";
import type { Lead, LeadListResponse } from "@/types/lead";

function normalizeSearchList(data: SearchListResponse | SearchJob[]): SearchJob[] {
  if (Array.isArray(data)) return data;
  return data.results || [];
}

function normalizeLeadList(data: LeadListResponse | Lead[]): Lead[] {
  if (Array.isArray(data)) return data;
  return data.results || [];
}

export const searchService = {
  async createSearch(payload: CreateSearchPayload) {
    const response = await api.post<CreateSearchResponse>(
      "/searches/create/",
      payload
    );

    if (response.data.search) {
      return response.data.search;
    }

    return {
      id: response.data.search_id,
      status: response.data.status,
      email_enrichment: response.data.email_enrichment
    } as SearchJob;
  },

  async getSearches() {
    const response = await api.get<SearchListResponse | SearchJob[]>(
      "/searches/list/"
    );

    return normalizeSearchList(response.data);
  },

  async getSearch(id: number | string) {
    const response = await api.get<SearchJob>(`/searches/${id}/`);
    return response.data;
  },

  async pauseSearch(id: number | string) {
    const response = await api.post(`/searches/${id}/pause/`);
    return response.data.search || response.data;
  },

  async resumeSearch(id: number | string) {
    const response = await api.post(`/searches/${id}/resume/`);
    return response.data.search || response.data;
  },

  async cancelSearch(id: number | string) {
    const response = await api.post(`/searches/${id}/cancel/`);
    return response.data.search || response.data;
  },

  async getSearchLeads(searchId: number | string) {
    const response = await api.get<LeadListResponse | Lead[]>("/leads/", {
      params: {
        search_id: searchId,
        page_size: 1000
      }
    });

    return normalizeLeadList(response.data);
  }
};