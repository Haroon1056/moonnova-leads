import { create } from "zustand";
import type { LeadFilters } from "@/types/lead";

interface LeadFiltersState {
  filters: LeadFilters;
  selectedLeadIds: number[];
  setFilter: <K extends keyof LeadFilters>(
    key: K,
    value: LeadFilters[K]
  ) => void;
  setFilters: (filters: Partial<LeadFilters>) => void;
  resetFilters: () => void;
  toggleSelectedLead: (leadId: number) => void;
  setSelectedLeadIds: (leadIds: number[]) => void;
  clearSelectedLeadIds: () => void;
}

const defaultFilters: LeadFilters = {
  search: "",
  keyword: "",
  location: "",
  category: "",
  has_email: "",
  has_website: "",
  no_website: "",
  broken_website: "",
  website_status: "",
  enrichment_status: "",
  ai_priority: "",
  is_favorite: "",
  min_lead_score: "",
  min_rating: "",
  page: 1,
  page_size: 50
};

export const useLeadFiltersStore = create<LeadFiltersState>((set) => ({
  filters: defaultFilters,
  selectedLeadIds: [],

  setFilter: (key, value) =>
    set((state) => ({
      filters: {
        ...state.filters,
        [key]: value,
        page: key === "page" ? Number(value) : 1
      }
    })),

  setFilters: (filters) =>
    set((state) => ({
      filters: {
        ...state.filters,
        ...filters,
        page: 1
      }
    })),

  resetFilters: () =>
    set({
      filters: defaultFilters
    }),

  toggleSelectedLead: (leadId) =>
    set((state) => {
      const selected = state.selectedLeadIds.includes(leadId);

      return {
        selectedLeadIds: selected
          ? state.selectedLeadIds.filter((id) => id !== leadId)
          : [...state.selectedLeadIds, leadId]
      };
    }),

  setSelectedLeadIds: (leadIds) =>
    set({
      selectedLeadIds: leadIds
    }),

  clearSelectedLeadIds: () =>
    set({
      selectedLeadIds: []
    })
}));