import { create } from "zustand";
import type { RealtimeEvent } from "@/lib/websocket";
import type { Lead } from "@/types/lead";
import type { SearchProgressEvent } from "@/types/search";

interface RealtimeState {
  connected: boolean;
  lastEvent: RealtimeEvent | null;
  liveLeads: Lead[];
  searchProgress: Record<number, SearchProgressEvent>;
  setConnected: (connected: boolean) => void;
  setLastEvent: (event: RealtimeEvent) => void;
  addLiveLead: (lead: Lead) => void;
  setSearchProgress: (searchId: number, progress: SearchProgressEvent) => void;
  clearLiveLeads: () => void;
}

export const useRealtimeStore = create<RealtimeState>((set) => ({
  connected: false,
  lastEvent: null,
  liveLeads: [],
  searchProgress: {},

  setConnected: (connected) => set({ connected }),

  setLastEvent: (event) => set({ lastEvent: event }),

  addLiveLead: (lead) =>
    set((state) => {
      const exists = state.liveLeads.some((item) => item.id === lead.id);

      if (exists) return state;

      return {
        liveLeads: [lead, ...state.liveLeads]
      };
    }),

  setSearchProgress: (searchId, progress) =>
    set((state) => ({
      searchProgress: {
        ...state.searchProgress,
        [searchId]: {
          ...state.searchProgress[searchId],
          ...progress
        }
      }
    })),

  clearLiveLeads: () => set({ liveLeads: [] })
}));