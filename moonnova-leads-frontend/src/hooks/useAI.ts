import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { aiService } from "@/services/ai.service";
import { useAuthStore } from "@/store/authStore";
import type { BulkAiPayload, SingleAiPayload } from "@/types/ai";

export function useAiUsage() {
  const accessToken = useAuthStore((state) => state.accessToken);

  return useQuery({
    queryKey: ["ai", "usage"],
    queryFn: aiService.getUsage,
    enabled: Boolean(accessToken),
    refetchInterval: 15000
  });
}

export function useAiJobs() {
  const accessToken = useAuthStore((state) => state.accessToken);

  return useQuery({
    queryKey: ["ai", "jobs"],
    queryFn: aiService.getJobs,
    enabled: Boolean(accessToken),
    refetchInterval: 5000
  });
}

export function useAiJob(jobId?: number | string) {
  const accessToken = useAuthStore((state) => state.accessToken);

  return useQuery({
    queryKey: ["ai", "jobs", jobId],
    queryFn: () => aiService.getJob(jobId!),
    enabled: Boolean(accessToken && jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;

      if (status === "pending" || status === "running") {
        return 3000;
      }

      return false;
    }
  });
}

export function useLeadAiInsight(leadId?: number | string) {
  const queryClient = useQueryClient();
  const accessToken = useAuthStore((state) => state.accessToken);

  const insightQuery = useQuery({
    queryKey: ["ai", "lead", leadId, "insight"],
    queryFn: () => aiService.getLeadInsight(leadId!),
    enabled: Boolean(accessToken && leadId),
    retry: false
  });

  const generateInsightMutation = useMutation({
    mutationFn: (payload: SingleAiPayload) =>
      aiService.generateLeadInsight(leadId!, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["ai", "lead", leadId, "insight"]
      });

      queryClient.invalidateQueries({
        queryKey: ["leads"]
      });

      queryClient.invalidateQueries({
        queryKey: ["ai", "usage"]
      });

      toast.success("AI insight generated");
    },
    onError: (error: any) => {
      const message =
        error?.response?.data?.detail ||
        error?.response?.data?.error ||
        "Failed to generate AI insight";

      toast.error(message);
    }
  });

  return {
    insightQuery,
    generateInsightMutation
  };
}

export function useBulkAiGeneration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: BulkAiPayload) => aiService.bulkGenerate(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ai", "jobs"] });
      queryClient.invalidateQueries({ queryKey: ["ai", "usage"] });
      queryClient.invalidateQueries({ queryKey: ["leads"] });

      toast.success("Bulk AI job started");
    },
    onError: (error: any) => {
      const message =
        error?.response?.data?.detail ||
        error?.response?.data?.error ||
        "Failed to start AI job";

      toast.error(message);
    }
  });
}