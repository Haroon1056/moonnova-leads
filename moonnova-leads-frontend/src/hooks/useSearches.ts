import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { searchService } from "@/services/search.service";
import { useAuthStore } from "@/store/authStore";
import type { CreateSearchPayload } from "@/types/search";

export function useSearches() {
  const queryClient = useQueryClient();
  const accessToken = useAuthStore((state) => state.accessToken);

  const searchesQuery = useQuery({
    queryKey: ["searches"],
    queryFn: searchService.getSearches,
    enabled: Boolean(accessToken),
    refetchInterval: 5000
  });

  const createSearchMutation = useMutation({
    mutationFn: (payload: CreateSearchPayload) =>
      searchService.createSearch(payload),
    onSuccess: (search) => {
      queryClient.invalidateQueries({ queryKey: ["searches"] });
      toast.success("Search started successfully");
      return search;
    },
    onError: (error: any) => {
      const message =
        error?.response?.data?.detail ||
        error?.response?.data?.error ||
        "Failed to start search";

      toast.error(message);
    }
  });

  return {
    searchesQuery,
    createSearchMutation
  };
}

export function useSearchDetail(id?: number | string) {
  const queryClient = useQueryClient();
  const accessToken = useAuthStore((state) => state.accessToken);

  const searchQuery = useQuery({
    queryKey: ["search", id],
    queryFn: () => searchService.getSearch(id!),
    enabled: Boolean(id && accessToken),
    refetchInterval: (query) => {
      const status = query.state.data?.status;

      if (status === "running" || status === "pending" || status === "paused") {
        return 3000;
      }

      return 8000;
    }
  });

  const searchLeadsQuery = useQuery({
    queryKey: ["search", id, "leads"],
    queryFn: () => searchService.getSearchLeads(id!),
    enabled: Boolean(id && accessToken),
    refetchInterval: 5000
  });

  const pauseMutation = useMutation({
    mutationFn: () => searchService.pauseSearch(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["search", id] });
      queryClient.invalidateQueries({ queryKey: ["searches"] });
      toast.success("Search paused");
    },
    onError: () => {
      toast.error("Failed to pause search");
    }
  });

  const resumeMutation = useMutation({
    mutationFn: () => searchService.resumeSearch(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["search", id] });
      queryClient.invalidateQueries({ queryKey: ["searches"] });
      toast.success("Search resumed");
    },
    onError: () => {
      toast.error("Failed to resume search");
    }
  });

  const cancelMutation = useMutation({
    mutationFn: () => searchService.cancelSearch(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["search", id] });
      queryClient.invalidateQueries({ queryKey: ["searches"] });
      toast.success("Search cancelled");
    },
    onError: () => {
      toast.error("Failed to cancel search");
    }
  });

  return {
    searchQuery,
    searchLeadsQuery,
    pauseMutation,
    resumeMutation,
    cancelMutation
  };
}