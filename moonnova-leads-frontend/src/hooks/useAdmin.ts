import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { adminService } from "@/services/admin.service";
import { useAuthStore } from "@/store/authStore";

function useIsAdmin() {
  const user = useAuthStore((state) => state.user);
  return Boolean(user?.is_staff || user?.is_superuser);
}

export function useAdminOverview() {
  const isAdmin = useIsAdmin();

  return useQuery({
    queryKey: ["admin", "overview"],
    queryFn: adminService.getOverview,
    enabled: isAdmin,
    refetchInterval: 15000
  });
}

export function useAdminUsers() {
  const isAdmin = useIsAdmin();

  return useQuery({
    queryKey: ["admin", "users"],
    queryFn: adminService.getUsers,
    enabled: isAdmin,
    refetchInterval: 30000
  });
}

export function useSystemHealth() {
  const isAdmin = useIsAdmin();

  return useQuery({
    queryKey: ["admin", "system-health"],
    queryFn: adminService.getSystemHealth,
    enabled: isAdmin,
    refetchInterval: 10000
  });
}

export function useMonitoringEvents() {
  const isAdmin = useIsAdmin();

  return useQuery({
    queryKey: ["admin", "monitoring-events"],
    queryFn: adminService.getMonitoringEvents,
    enabled: isAdmin,
    refetchInterval: 10000
  });
}

export function useAdminAiSummary() {
  const isAdmin = useIsAdmin();

  return useQuery({
    queryKey: ["admin", "ai-summary"],
    queryFn: adminService.getAiSummary,
    enabled: isAdmin,
    refetchInterval: 15000
  });
}

export function useAdminAiJobs() {
  const isAdmin = useIsAdmin();

  return useQuery({
    queryKey: ["admin", "ai-jobs"],
    queryFn: adminService.getAiJobs,
    enabled: isAdmin,
    refetchInterval: 10000
  });
}

export function useAdminSearches() {
  const isAdmin = useIsAdmin();

  return useQuery({
    queryKey: ["admin", "searches"],
    queryFn: adminService.getSearches,
    enabled: isAdmin,
    refetchInterval: 15000
  });
}

export function useAdminUserActions() {
  const queryClient = useQueryClient();

  const activateUserMutation = useMutation({
    mutationFn: (userId: number | string) => adminService.activateUser(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
      toast.success("User activated");
    },
    onError: () => {
      toast.error("Failed to activate user");
    }
  });

  const suspendUserMutation = useMutation({
    mutationFn: (userId: number | string) => adminService.suspendUser(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
      toast.success("User suspended");
    },
    onError: () => {
      toast.error("Failed to suspend user");
    }
  });

  return {
    activateUserMutation,
    suspendUserMutation
  };
}