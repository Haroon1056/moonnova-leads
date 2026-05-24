import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { exportService } from "@/services/export.service";
import { useAuthStore } from "@/store/authStore";
import type { CreateExportPayload, ExportHistory } from "@/types/export";

export function useExports() {
  const queryClient = useQueryClient();
  const accessToken = useAuthStore((state) => state.accessToken);

  const exportsQuery = useQuery({
    queryKey: ["exports"],
    queryFn: exportService.getExports,
    enabled: Boolean(accessToken),
    refetchInterval: 5000
  });

  const createExportMutation = useMutation({
    mutationFn: (payload: CreateExportPayload) =>
      exportService.createExport(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exports"] });
      toast.success("Export started");
    },
    onError: (error: any) => {
      const message =
        error?.response?.data?.detail ||
        error?.response?.data?.error ||
        "Failed to start export";

      toast.error(message);
    }
  });

  const downloadExportMutation = useMutation({
    mutationFn: (exportItem: ExportHistory) =>
      exportService.downloadExport(exportItem),
    onSuccess: () => {
      toast.success("Download started");
    },
    onError: (error: any) => {
      const message =
        error?.response?.data?.detail ||
        error?.response?.data?.error ||
        "Failed to download export";

      toast.error(message);
    }
  });

  const deleteExportMutation = useMutation({
    mutationFn: (id: number | string) => exportService.deleteExport(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exports"] });
      toast.success("Export deleted");
    },
    onError: () => {
      toast.error("Failed to delete export");
    }
  });

  return {
    exportsQuery,
    createExportMutation,
    downloadExportMutation,
    deleteExportMutation
  };
}