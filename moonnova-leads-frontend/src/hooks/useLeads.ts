import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { leadService } from "@/services/lead.service";
import { useLeadFiltersStore } from "@/store/leadFiltersStore";
import { useAuthStore } from "@/store/authStore";
import type { Lead } from "@/types/lead";

export function useLeads() {
  const queryClient = useQueryClient();
  const accessToken = useAuthStore((state) => state.accessToken);
  const filters = useLeadFiltersStore((state) => state.filters);
  const selectedLeadIds = useLeadFiltersStore((state) => state.selectedLeadIds);
  const clearSelectedLeadIds = useLeadFiltersStore(
    (state) => state.clearSelectedLeadIds
  );

  const leadsQuery = useQuery({
    queryKey: ["leads", filters],
    queryFn: () => leadService.getLeads(filters),
    enabled: Boolean(accessToken),
    refetchInterval: 8000
  });

  const updateLeadMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<Lead> }) =>
      leadService.updateLead(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leads"] });
      toast.success("Lead updated");
    },
    onError: () => {
      toast.error("Failed to update lead");
    }
  });

  const enrichLeadMutation = useMutation({
    mutationFn: (id: number) => leadService.enrichLead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leads"] });
      toast.success("Lead enrichment started");
    },
    onError: () => {
      toast.error("Failed to start enrichment");
    }
  });

  const bulkEnrichMutation = useMutation({
    mutationFn: (leadIds: number[]) => leadService.bulkEnrichLeadWebsites(leadIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leads"] });
      toast.success("Bulk enrichment started");
      clearSelectedLeadIds();
    },
    onError: () => {
      toast.error("Failed to start bulk enrichment");
    }
  });

  const markFavoriteMutation = useMutation({
    mutationFn: (leadIds: number[]) => leadService.markFavorite(leadIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leads"] });
      toast.success("Marked as favorite");
      clearSelectedLeadIds();
    },
    onError: () => {
      toast.error("Failed to mark favorite");
    }
  });

  const unmarkFavoriteMutation = useMutation({
    mutationFn: (leadIds: number[]) => leadService.unmarkFavorite(leadIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leads"] });
      toast.success("Removed from favorites");
      clearSelectedLeadIds();
    },
    onError: () => {
      toast.error("Failed to update favorites");
    }
  });

  const deleteLeadsMutation = useMutation({
    mutationFn: (leadIds: number[]) => leadService.deleteLeads(leadIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leads"] });
      toast.success("Leads deleted");
      clearSelectedLeadIds();
    },
    onError: () => {
      toast.error("Failed to delete leads");
    }
  });

  return {
    filters,
    selectedLeadIds,
    leadsQuery,
    updateLeadMutation,
    enrichLeadMutation,
    bulkEnrichMutation,
    markFavoriteMutation,
    unmarkFavoriteMutation,
    deleteLeadsMutation
  };
}

export function useLeadLists() {
  const queryClient = useQueryClient();
  const accessToken = useAuthStore((state) => state.accessToken);

  const leadListsQuery = useQuery({
    queryKey: ["lead-lists"],
    queryFn: leadService.getLeadLists,
    enabled: Boolean(accessToken)
  });

  const createLeadListMutation = useMutation({
    mutationFn: (payload: { name: string; description?: string }) =>
      leadService.createLeadList(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lead-lists"] });
      toast.success("Lead list created");
    },
    onError: () => {
      toast.error("Failed to create lead list");
    }
  });

  const addLeadsToListMutation = useMutation({
    mutationFn: ({
      listId,
      leadIds
    }: {
      listId: number | string;
      leadIds: number[];
    }) => leadService.addLeadsToList(listId, leadIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lead-lists"] });
      toast.success("Leads added to list");
    },
    onError: () => {
      toast.error("Failed to add leads to list");
    }
  });

  return {
    leadListsQuery,
    createLeadListMutation,
    addLeadsToListMutation
  };
}