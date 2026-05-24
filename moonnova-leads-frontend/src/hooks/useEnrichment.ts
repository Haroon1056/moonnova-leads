import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { enrichmentService } from "@/services/enrichment.service";
import { useAuthStore } from "@/store/authStore";

export function useSearchEnrichment(searchId?: number | string) {
  const queryClient = useQueryClient();
  const accessToken = useAuthStore((state) => state.accessToken);

  const enrichmentJobQuery = useQuery({
    queryKey: ["search", searchId, "enrichment-job"],
    queryFn: () => enrichmentService.getSearchEnrichmentJob(searchId!),
    enabled: Boolean(searchId && accessToken),
    refetchInterval: (query) => {
      const status = query.state.data?.status;

      if (status === "pending" || status === "running") {
        return 3000;
      }

      return 8000;
    }
  });

  const startEnrichmentMutation = useMutation({
    mutationFn: () => enrichmentService.startSearchEnrichment(searchId!),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["search", searchId, "enrichment-job"]
      });

      queryClient.invalidateQueries({
        queryKey: ["search", searchId, "leads"]
      });

      toast.success("Enrichment started");
    },
    onError: (error: any) => {
      const message =
        error?.response?.data?.detail ||
        error?.response?.data?.error ||
        "Failed to start enrichment";

      toast.error(message);
    }
  });

  return {
    enrichmentJobQuery,
    startEnrichmentMutation
  };
}